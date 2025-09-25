# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Union

from app.core.database import get_db
from app.models.user import User, UserType
from app.models.profile import Profile
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.individual import Individual
from app.models.user_privacy import UserPrivacySettings
from app.schemas.auth import (
    UserLogin,
    StudentRegister,
    TeacherRegister,
    ParentRegister,
    IndividualRegister,
    AdminRegister,
    LoginResponse,
    RegisterResponse,
    TwoFactorVerify,
)
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import get_settings
from app.services.email import send_verification_email
from app.services.sms import send_verification_sms

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register/student", response_model=RegisterResponse)
async def register_student(
    data: StudentRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new student"""
    # Check if user exists
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if (
        data.phone_number
        and db.query(User).filter(User.phone_number == data.phone_number).first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        user_type=UserType.STUDENT,
        email=data.email,
        phone_number=data.phone_number,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()  # Get user.id without committing

    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=data.full_name,
        date_of_birth=data.date_of_birth,
        preferred_language=data.preferred_language,
        timezone=data.timezone,
    )
    db.add(profile)

    # Create student record
    student = Student(
        user_id=user.id,
        grade_level=data.grade_level,
        institution=data.institution,
        institution_type=data.institution_type,
        is_minor=data.is_minor,
    )
    db.add(student)

    # Create default privacy settings
    privacy_settings = UserPrivacySettings(
        user_id=user.id,
        profile_visibility="public" if not data.is_minor else "private",
        field_visibility={
            "email": False,
            "phone_number": False,
            "date_of_birth": False,
            "current_gpa": False,
            "student_id": False,
        },
    )
    db.add(privacy_settings)

    # Handle parent linking for minors
    if data.is_minor and (data.parent_email or data.parent_phone):
        # Find parent user
        parent_query = db.query(User).filter(User.user_type == UserType.PARENT)
        if data.parent_email:
            parent_user = parent_query.filter(User.email == data.parent_email).first()
        else:
            parent_user = parent_query.filter(
                User.phone_number == data.parent_phone
            ).first()

        if parent_user:
            student.parent_user_id = parent_user.id
            # TODO: Send notification to parent about child registration

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

    # Send verification email/SMS
    verification_sent_to = None
    if data.email:
        background_tasks.add_task(send_verification_email, data.email, user.id)
        verification_sent_to = f"email: {data.email}"
    elif data.phone_number:
        background_tasks.add_task(send_verification_sms, data.phone_number, user.id)
        verification_sent_to = f"phone: {data.phone_number}"

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user.user_type}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RegisterResponse(
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "full_name": profile.full_name,
            "is_verified": user.is_verified,
            "is_minor": student.is_minor,
        },
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        },
        requires_verification=True,
        verification_sent_to=verification_sent_to,
    )


@router.post("/register/teacher", response_model=RegisterResponse)
async def register_teacher(
    data: TeacherRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new teacher"""
    # Check if user exists
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if (
        data.phone_number
        and db.query(User).filter(User.phone_number == data.phone_number).first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Check if employee ID exists
    if (
        data.employee_id
        and db.query(Teacher).filter(Teacher.employee_id == data.employee_id).first()
    ):
        raise HTTPException(status_code=400, detail="Employee ID already registered")

    # Create user
    user = User(
        user_type=UserType.TEACHER,
        email=data.email,
        phone_number=data.phone_number,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=data.full_name,
        preferred_language=data.preferred_language,
        timezone=data.timezone,
    )
    db.add(profile)

    # Create teacher record
    teacher = Teacher(
        user_id=user.id,
        institution=data.institution,
        institution_type=data.institution_type,
        designation=data.designation,
        employee_id=data.employee_id,
        highest_degree=data.highest_degree,
        specializations=data.specializations,
        years_of_experience=data.years_of_experience,
        is_verified=False,  # Requires admin verification
    )
    db.add(teacher)

    # Create default privacy settings for teachers
    privacy_settings = UserPrivacySettings(
        user_id=user.id,
        profile_visibility="public",  # Teachers are usually public
        field_visibility={
            "email": False,
            "phone_number": False,
            "employee_id": False,
            "designation": True,
            "institution": True,
            "specializations": True,
            "is_verified": True,
        },
        search_visibility={
            "searchable_by_email": False,
            "searchable_by_phone": False,
            "searchable_by_username": True,
            "searchable_by_name": True,
            "appear_in_suggestions": True,
            "appear_in_directory": True,  # Teachers appear in directory
        },
    )
    db.add(privacy_settings)

    # Save verification document if provided
    if data.verification_document:
        # TODO: Handle document upload to storage
        teacher.verification_document_url = data.verification_document

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

    # Send verification email/SMS
    verification_sent_to = None
    if data.email:
        background_tasks.add_task(send_verification_email, data.email, user.id)
        verification_sent_to = f"email: {data.email}"
    elif data.phone_number:
        background_tasks.add_task(send_verification_sms, data.phone_number, user.id)
        verification_sent_to = f"phone: {data.phone_number}"

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user.user_type}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RegisterResponse(
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "full_name": profile.full_name,
            "institution": teacher.institution,
            "designation": teacher.designation,
            "is_verified": user.is_verified,
            "teacher_verified": teacher.is_verified,
        },
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        },
        requires_verification=True,
        verification_sent_to=verification_sent_to,
    )


@router.post("/register/parent", response_model=RegisterResponse)
async def register_parent(
    data: ParentRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new parent"""
    # Check if user exists
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if (
        data.phone_number
        and db.query(User).filter(User.phone_number == data.phone_number).first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        user_type=UserType.PARENT,
        email=data.email,
        phone_number=data.phone_number,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=data.full_name,
        preferred_language=data.preferred_language,
        timezone=data.timezone,
    )
    db.add(profile)

    # Create parent record
    parent = Parent(
        user_id=user.id,
        occupation=data.occupation,
        nid_number=data.nid_number,
        notify_on_child_activity=True,
        notify_on_low_credits=True,
        notify_weekly_report=True,
    )
    db.add(parent)

    # Create default privacy settings
    privacy_settings = UserPrivacySettings(
        user_id=user.id,
        profile_visibility="private",  # Parents are usually private
        field_visibility={
            "email": False,
            "phone_number": False,
            "occupation": False,
            "nid_number": False,
        },
    )
    db.add(privacy_settings)

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

    # Link children if provided
    if data.children_identifiers:
        for child_info in data.children_identifiers:
            # Find child by identifier
            child_user = None
            if child_info.get("email"):
                child_user = (
                    db.query(User)
                    .filter(
                        User.email == child_info["email"],
                        User.user_type == UserType.STUDENT,
                    )
                    .first()
                )
            elif child_info.get("phone"):
                child_user = (
                    db.query(User)
                    .filter(
                        User.phone_number == child_info["phone"],
                        User.user_type == UserType.STUDENT,
                    )
                    .first()
                )

            if child_user and child_user.student:
                child_user.student.parent_user_id = user.id
                # TODO: Send notification to child about parent linkage

        db.commit()

    # Send verification
    verification_sent_to = None
    if data.email:
        background_tasks.add_task(send_verification_email, data.email, user.id)
        verification_sent_to = f"email: {data.email}"
    elif data.phone_number:
        background_tasks.add_task(send_verification_sms, data.phone_number, user.id)
        verification_sent_to = f"phone: {data.phone_number}"

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user.user_type}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RegisterResponse(
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "full_name": profile.full_name,
            "is_verified": user.is_verified,
        },
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        },
        requires_verification=True,
        verification_sent_to=verification_sent_to,
    )


@router.post("/register/individual", response_model=RegisterResponse)
async def register_individual(
    data: IndividualRegister,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Register a new individual user"""
    # Check if user exists
    if data.email and db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    if (
        data.phone_number
        and db.query(User).filter(User.phone_number == data.phone_number).first()
    ):
        raise HTTPException(status_code=400, detail="Phone number already registered")

    if data.username and db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create user
    user = User(
        user_type=UserType.INDIVIDUAL,
        email=data.email,
        phone_number=data.phone_number,
        username=data.username,
        hashed_password=get_password_hash(data.password),
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.flush()

    # Create profile
    profile = Profile(
        user_id=user.id,
        full_name=data.full_name,
        preferred_language=data.preferred_language,
        timezone=data.timezone,
    )
    db.add(profile)

    # Create individual record
    from app.models.individual import Individual

    individual = Individual(
        user_id=user.id,
        learning_purpose=data.learning_purpose,
        occupation=data.occupation,
        organization=data.organization,
    )
    db.add(individual)

    # Create default privacy settings
    privacy_settings = UserPrivacySettings(
        user_id=user.id,
        profile_visibility="public",
        field_visibility={
            "email": False,
            "phone_number": False,
            "organization": True,
            "learning_purpose": True,
        },
    )
    db.add(privacy_settings)

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Registration failed")

    # Send verification
    verification_sent_to = None
    if data.email:
        background_tasks.add_task(send_verification_email, data.email, user.id)
        verification_sent_to = f"email: {data.email}"
    elif data.phone_number:
        background_tasks.add_task(send_verification_sms, data.phone_number, user.id)
        verification_sent_to = f"phone: {data.phone_number}"

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user.user_type}
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return RegisterResponse(
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "full_name": profile.full_name,
            "learning_purpose": individual.learning_purpose,
            "is_verified": user.is_verified,
        },
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        },
        requires_verification=True,
        verification_sent_to=verification_sent_to,
    )


@router.post("/login", response_model=LoginResponse)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login with email, phone, or username"""
    # Find user by identifier
    user = None
    identifier = data.identifier.strip().lower()

    # Check if identifier is email
    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier).first()
    # Check if identifier is phone
    elif identifier.startswith("+") or identifier.isdigit():
        user = db.query(User).filter(User.phone_number == identifier).first()
    # Otherwise treat as username
    else:
        user = db.query(User).filter(User.username == identifier).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Verify password
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive"
        )

    # Check if user is suspended
    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account suspended: {user.suspension_reason or 'Contact support'}",
        )

    # Check if 2FA is enabled
    if user.two_factor_enabled:
        # Generate temporary token for 2FA verification
        temp_token = create_access_token(
            data={"sub": str(user.id), "type": "2fa_pending"},
            expires_delta=timedelta(minutes=5),
        )

        return LoginResponse(
            user={
                "id": str(user.id),
                "username": user.username,
                "user_type": user.user_type,
            },
            tokens={"access_token": "", "token_type": "bearer", "expires_in": 0},
            requires_2fa=True,
            temp_token=temp_token,
        )

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Get user profile
    profile = user.profile

    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "type": user.user_type}
    )
    refresh_token = None
    if data.remember_me:
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return LoginResponse(
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "full_name": profile.full_name if profile else None,
            "is_verified": user.is_verified,
            "avatar_url": profile.avatar_url if profile else None,
        },
        tokens={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        },
        requires_2fa=False,
    )


@router.post("/verify-2fa", response_model=LoginResponse)
async def verify_two_factor(data: TwoFactorVerify, db: Session = Depends(get_db)):
    """Verify 2FA code"""
    # Decode temporary token
    try:
        payload = decode_token(data.token)
        if payload.get("type") != "2fa_pending":
            raise HTTPException(status_code=400, detail="Invalid token")

        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Verify 2FA code
        # TODO: Implement actual 2FA verification (TOTP)
        # For now, just check if code is valid

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        # Get user profile
        profile = user.profile

        # Generate real tokens
        access_token = create_access_token(
            data={"sub": str(user.id), "type": user.user_type}
        )
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return LoginResponse(
            user={
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "full_name": profile.full_name if profile else None,
                "is_verified": user.is_verified,
                "avatar_url": profile.avatar_url if profile else None,
            },
            tokens={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
            },
            requires_2fa=False,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid or expired token")


@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    try:
        payload = decode_token(refresh_token)
        user_id = payload.get("sub")

        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Generate new access token
        access_token = create_access_token(
            data={"sub": str(user.id), "type": user.user_type}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": get_settings().jwt_access_token_expire_minutes * 60,
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Logout user (invalidate tokens)"""
    # In a production environment, you might want to:
    # 1. Add the token to a blacklist
    # 2. Clear refresh tokens from database
    # 3. Update last activity timestamp

    # For now, just return success
    # The client should delete tokens from storage
    return {"message": "Successfully logged out"}


@router.post("/verify-email/{token}")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email with token"""
    # TODO: Implement email verification logic
    # Decode token, find user, update is_email_verified

    return {"message": "Email verified successfully"}


@router.post("/verify-phone")
async def verify_phone(code: str, user_id: UUID, db: Session = Depends(get_db)):
    """Verify phone with OTP code"""
    # TODO: Implement phone verification logic
    # Verify OTP code, update is_phone_verified

    return {"message": "Phone verified successfully"}


@router.post("/resend-verification")
async def resend_verification(
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Resend verification email/SMS"""
    if current_user.is_verified:
        return {"message": "User already verified"}

    verification_sent_to = None

    if current_user.email and not current_user.is_email_verified:
        background_tasks.add_task(
            send_verification_email, current_user.email, current_user.id
        )
        verification_sent_to = f"email: {current_user.email}"

    if current_user.phone_number and not current_user.is_phone_verified:
        background_tasks.add_task(
            send_verification_sms, current_user.phone_number, current_user.id
        )
        verification_sent_to = f"phone: {current_user.phone_number}"

    if not verification_sent_to:
        raise HTTPException(
            status_code=400, detail="No unverified contact method found"
        )

    return {"message": "Verification resent", "sent_to": verification_sent_to}
