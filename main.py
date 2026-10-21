import asyncio
import logging
import sys
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, 
    InlineKeyboardButton, FSInputFile
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

import database as db
from pdf_generator import generate_attendance_pdf
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


class CourseSetup(StatesGroup):
    waiting_for_instructor_name = State()
    waiting_for_department = State()
    waiting_for_course_title = State()
    waiting_for_year_semester = State()

class StudentRegistration(StatesGroup):
    waiting_for_name = State()
    waiting_for_student_id = State()

class StudentPINEntry(StatesGroup):
    waiting_for_pin = State()

class LeaveRequestForm(StatesGroup):
    waiting_for_date = State()
    waiting_for_reason = State()


def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="[ INSTRUCTOR PORTAL ]", callback_data="portal_instructor")],
        [InlineKeyboardButton(text="[ STUDENT PORTAL ]", callback_data="portal_student")]
    ])

def get_instructor_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Create New Course", callback_data="instructor_create_course")],
        [InlineKeyboardButton(text="View Active Courses & Sessions", callback_data="instructor_view_courses")]
    ])

def get_student_portal_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="[ Check In (Enter PIN) ]", callback_data="student_checkin")],
        [InlineKeyboardButton(text="[ Request Permission / Leave ]", callback_data="student_leave")]
    ])


@dp.message(CommandStart())
async def handle_start(message: Message, command: CommandObject, state: FSMContext):
    args = command.args
    
    
    if args and args.startswith("enroll_"):
        course_code = args.replace("enroll_", "")
        await state.update_data(enrolling_course_code=course_code)
        await state.set_state(StudentRegistration.waiting_for_name)
        
        await message.answer(
            "DIRE DAWA UNIVERSITY\n"
            "OFFICIAL COURSE ENROLLMENT PORTAL\n"
            "========================================\n"
            f"Course Identifier: {course_code}\n\n"
            "Enter your Full Legal Name (as registered with the registrar):"
        )
        return

    
    await state.clear()
    await message.answer(
        "DIRE DAWA UNIVERSITY\n"
        "ATTENDANCE MANAGEMENT SYSTEM\n"
        "========================================\n"
        "System Status: [ONLINE]\n"
        "Select your authorized role to proceed:",
        reply_markup=get_main_menu_keyboard()
    )


@dp.callback_query(F.data == "portal_instructor")
async def show_instructor_portal(callback: CallbackQuery):
    await callback.message.edit_text(
        "DIRE DAWA UNIVERSITY | INSTRUCTOR DASHBOARD\n"
        "========================================\n"
        "Authorized Faculty Access.\n"
        "Select an action to proceed:",
        reply_markup=get_instructor_menu_keyboard()
    )

@dp.callback_query(F.data == "instructor_create_course")
async def start_course_creation(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CourseSetup.waiting_for_instructor_name)
    await callback.message.answer(
        "Course Initialization (Step 1 of 4)\n"
        "----------------------------------------\n"
        "Enter Instructor Name & Academic Title\n"
        "(Format: Ins. Full Name or Dr. Full Name):"
    )

@dp.message(CourseSetup.waiting_for_instructor_name)
async def process_inst_name(message: Message, state: FSMContext):
    await state.update_data(instructor_name=message.text.strip().title())
    await state.set_state(CourseSetup.waiting_for_department)
    await message.answer(
        "Course Initialization (Step 2 of 4)\n"
        "----------------------------------------\n"
        "Enter Academic Department\n"
        "(e.g., Computer Science, Electrical Engineering):"
    )

@dp.message(CourseSetup.waiting_for_department)
async def process_dept(message: Message, state: FSMContext):
    await state.update_data(department=message.text.strip().title())
    await state.set_state(CourseSetup.waiting_for_course_title)
    await message.answer(
        "Course Initialization (Step 3 of 4)\n"
        "----------------------------------------\n"
        "Enter Official Course Title\n"
        "(e.g., Data Structures and Algorithms):"
    )

@dp.message(CourseSetup.waiting_for_course_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(course_name=message.text.strip().title())
    await state.set_state(CourseSetup.waiting_for_year_semester)
    await message.answer(
        "Course Initialization (Step 4 of 4)\n"
        "----------------------------------------\n"
        "Enter Target Academic Year & Semester\n"
        "(e.g., Year 3, Semester 1 or Remedial Program):"
    )

@dp.message(CourseSetup.waiting_for_year_semester)
async def process_year_sem(message: Message, state: FSMContext):
    year_semester = message.text.strip().title()
    data = await state.get_data()
    
    instructor_name = data.get("instructor_name")
    department = data.get("department")
    course_name = data.get("course_name")
    teacher_id = message.from_user.id
    
    course_code = db.create_course(teacher_id, instructor_name, department, course_name, year_semester)
    await state.clear()
    
    bot_info = await bot.get_me()
    enrollment_link = f"https://t.me/{bot_info.username}?start=enroll_{course_code}"
    
    await message.answer(
        "DIRE DAWA UNIVERSITY | COURSE RECORD CREATED\n"
        "========================================\n"
        f"Course Title:   {course_name}\n"
        f"Course Code:    {course_code}\n"
        f"Instructor:     {instructor_name}\n"
        f"Department:     {department}\n"
        f"Academic Term:  {year_semester}\n"
        "Status:         [ACTIVE]\n"
        "========================================\n\n"
        "OFFICIAL ENROLLMENT INVITATION NOTICE:\n"
        "(Forward the following notice to the Class Representative)\n\n"
        f"Attention: Students of {course_name} ({year_semester})\n"
        "Please use the official registration link below to verify your student account for attendance tracking:\n"
        f"{enrollment_link}"
    )



@dp.callback_query(F.data == "instructor_view_courses")
async def show_course_selector(callback: CallbackQuery):
    courses = db.get_instructor_courses(callback.from_user.id)
    
    if not courses:
        await callback.message.edit_text(
            "DIRE DAWA UNIVERSITY | INSTRUCTOR PORTAL\n"
            "----------------------------------------\n"
            "No registered courses found.\n"
            "Tap 'Create New Course' to initialize a class.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Create New Course", callback_data="instructor_create_course")],
                [InlineKeyboardButton(text="[ Back ]", callback_data="portal_instructor")]
            ])
        )
        return
        
    course_buttons = []
    for code, title, dept, batch in courses:
        enrolled_count = db.get_enrolled_count(code)
        course_buttons.append([
            InlineKeyboardButton(
                text=f"{title} ({batch}) [{enrolled_count} Students]",
                callback_data=f"manage_course:{code}"
            )
        ])
    course_buttons.append([InlineKeyboardButton(text="[ Back to Dashboard ]", callback_data="portal_instructor")])
    
    await callback.message.edit_text(
        "DIRE DAWA UNIVERSITY | COURSE SELECTOR\n"
        "========================================\n"
        "Select the course you are currently teaching:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=course_buttons)
    )

@dp.callback_query(F.data.startswith("manage_course:"))
async def manage_selected_course(callback: CallbackQuery):
    course_code = callback.data.split(":")[1]
    course_info = db.get_course_details(course_code)
    
    if not course_info:
        await callback.answer("Course record not found.")
        return
        
    title, instructor, dept, batch = course_info
    enrolled_count = db.get_enrolled_count(course_code)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="[ Start In-Class Attendance ]", callback_data=f"start_session:{course_code}")],
        [InlineKeyboardButton(text="[ View Enrolled Student Roster ]", callback_data=f"roster:{course_code}")],
        [InlineKeyboardButton(text="[ Check 3-Absence Warnings ]", callback_data=f"warnings:{course_code}")],
        [InlineKeyboardButton(text="[ Back to Course List ]", callback_data="instructor_view_courses")]
    ])
    
    await callback.message.edit_text(
        "DIRE DAWA UNIVERSITY | CLASS DASHBOARD\n"
        "========================================\n"
        f"Course Title:   {title}\n"
        f"Course Code:    {course_code}\n"
        f"Department:     {dept}\n"
        f"Academic Term:  {batch}\n"
        f"Total Enrolled: {enrolled_count} Students\n"
        "========================================\n"
        "Select an action for this specific class:",
        reply_markup=keyboard
    )


@dp.callback_query(F.data.startswith("roster:"))
async def view_course_roster(callback: CallbackQuery):
    course_code = callback.data.split(":")[1]
    students = db.get_all_enrolled_students(course_code)
    
    if not students:
        await callback.message.answer(f"No students have enrolled in {course_code} yet.")
        return
        
    roster_text = (
        f"DIRE DAWA UNIVERSITY | ENROLLED ROSTER\n"
        f"Course Code: {course_code} | Total: {len(students)} Students\n"
        "========================================\n"
    )
    for idx, (stu_id, name) in enumerate(students, 1):
        roster_text += f"{idx}. {name} ({stu_id})\n"
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="[ Back to Class Dashboard ]", callback_data=f"manage_course:{course_code}")]
    ])
    await callback.message.answer(roster_text, reply_markup=keyboard)



@dp.callback_query(F.data.startswith("start_session:"))
async def start_attendance_session(callback: CallbackQuery):
    course_code = callback.data.split(":")[1]
    total_enrolled = db.get_enrolled_count(course_code)
    
    if total_enrolled == 0:
        await callback.message.answer("Error: Cannot start session. No students are currently enrolled in this course.")
        return
        
    session_id, pin, expires_at = db.create_session(course_code, duration_seconds=60)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="[ End Session Now & Close Window ]", callback_data=f"force_close:{session_id}:{course_code}")]
    ])
    
    session_msg = await callback.message.answer(
        "DIRE DAWA UNIVERSITY | ACTIVE ATTENDANCE SESSION\n"
        "========================================\n"
        f"Course Code:    {course_code}\n"
        f"SESSION PIN:    [ {pin} ]\n"
        "Window Status:  OPEN (60 Seconds)\n"
        f"Total Enrolled: {total_enrolled} Students\n"
        "========================================\n"
        "Students in this class can now enter this 4-digit PIN directly into the chat.",
        reply_markup=keyboard
    )
    
    asyncio.create_task(run_session_countdown(session_id, course_code, session_msg, total_enrolled))

async def run_session_countdown(session_id: int, course_code: str, message: Message, total_enrolled: int):
    await asyncio.sleep(60)
    db.close_session(session_id)
    await display_session_summary(message, session_id, course_code, total_enrolled)

@dp.callback_query(F.data.startswith("force_close:"))
async def handle_force_close(callback: CallbackQuery):
    _, session_id, course_code = callback.data.split(":")
    session_id = int(session_id)
    total_enrolled = db.get_enrolled_count(course_code)
    db.close_session(session_id)
    await callback.message.answer("Attendance session manually closed by instructor.")
    await display_session_summary(callback.message, session_id, course_code, total_enrolled)

async def display_session_summary(message: Message, session_id: int, course_code: str, total_enrolled: int):
    present_students = db.get_present_students(session_id)
    absent_students = db.get_absent_students(session_id, course_code)
    present_count = len(present_students)
    absent_count = len(absent_students)
    
    summary_text = (
        "DIRE DAWA UNIVERSITY | SESSION CLOSED\n"
        "========================================\n"
        f"Course Code:    {course_code}\n"
        f"Final Tally:    {present_count} / {total_enrolled} Present\n"
        f"Unmarked:       {absent_count} Students\n"
        "========================================\n"
    )
    
    keyboard_buttons = []
    if absent_students:
        summary_text += "\nUNCHECKED / DEAD PHONE LIST:\n"
        for stu_id, name in absent_students:
            summary_text += f"- {name} ({stu_id})\n"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"Mark Present: {name}", 
                    callback_data=f"dead_mark:{session_id}:{course_code}:{stu_id}"
                )
            ])
            
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="[ Finalize & Export Official PDF ]", 
            callback_data=f"export_pdf:{session_id}:{course_code}"
        )
    ])
    
    await message.answer(summary_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons))



@dp.callback_query(F.data.startswith("dead_mark:"))
async def handle_dead_phone_override(callback: CallbackQuery):
    _, session_id, course_code, student_id = callback.data.split(":")
    session_id = int(session_id)
    
    all_students = db.get_all_enrolled_students(course_code)
    student_name = next((name for s_id, name in all_students if s_id == student_id), "Student")
    
    success = db.record_attendance(session_id, course_code, student_id, student_name, method="TEACHER_MANUAL")
    
    if success:
        await callback.answer(f"Status Updated: {student_name} marked PRESENT.")
        await callback.message.answer(
            f"AUDIT LOG: {student_name} ({student_id}) verified and marked PRESENT via Instructor Manual Override."
        )
    else:
        await callback.answer("Record already exists.")



@dp.callback_query(F.data.startswith("export_pdf:"))
async def handle_pdf_export(callback: CallbackQuery):
    _, session_id, course_code = callback.data.split(":")
    session_id = int(session_id)
    
    await callback.message.answer("Generating Official University PDF Dossier...")
    
    course_info = db.get_course_details(course_code)
    course_name, instructor_name, department, year_semester = course_info
    
    present_list = db.get_present_students(session_id)
    absent_list = db.get_absent_students(session_id, course_code)
    
    attendance_rows = []
    for s_id, name, time_str, method in present_list:
        attendance_rows.append((s_id, name, "PRESENT", method))
    for s_id, name in absent_list:
        attendance_rows.append((s_id, name, "ABSENT", "-"))
        
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%I:%M %p")
    filename = f"DDU_Attendance_{course_code}_{date_str}.pdf"
    
    generate_attendance_pdf(
        course_name=course_name,
        course_code=course_code,
        instructor_name=instructor_name,
        department=department,
        year_semester=year_semester,
        date_str=date_str,
        time_str=time_str,
        attendance_rows=attendance_rows,
        output_filename=filename
    )
    
    pdf_file = FSInputFile(filename)
    await callback.message.answer_document(
        document=pdf_file,
        caption=(
            "DIRE DAWA UNIVERSITY | OFFICIAL DOSSIER\n"
            f"Course: {course_name} ({course_code})\n"
            f"Instructor: {instructor_name}\n"
            f"Session Date: {date_str} at {time_str}\n"
            "Status: Validated & Signed"
        )
    )
    
    if os.path.exists(filename):
        os.remove(filename)


@dp.callback_query(F.data.startswith("warnings:"))
async def handle_warnings(callback: CallbackQuery):
    course_code = callback.data.split(":")[1]
    warnings = db.get_critical_absences(course_code, threshold=3)
    
    if not warnings:
        await callback.message.answer(
            f"DIRE DAWA UNIVERSITY | ACADEMIC RECORD\n"
            f"Course Code: {course_code}\n"
            "----------------------------------------\n"
            "No students have exceeded the 3-absence disciplinary threshold."
        )
        return
        
    warning_text = (
        "DIRE DAWA UNIVERSITY | CRITICAL ATTENDANCE ALERTS\n"
        "========================================\n"
        f"Course Code: {course_code}\n"
        "Threshold: 3 Missed Sessions (Disciplinary Warning)\n"
        "========================================\n"
    )
    for stu_id, name, missed_count in warnings:
        warning_text += f"- {name} ({stu_id}) -- Total Missed: {missed_count} Sessions\n"
        
    await callback.message.answer(warning_text)


@dp.message(StudentRegistration.waiting_for_name)
async def process_student_name(message: Message, state: FSMContext):
    name = message.text.strip().title()
    await state.update_data(full_name=name)
    await state.set_state(StudentRegistration.waiting_for_student_id)
    await message.answer(
        f"Name Verified: {name}\n\n"
        "Enter your official DDU Student ID Number\n"
        "(Format: RMD2534 or DDU1601456):"
    )

@dp.message(StudentRegistration.waiting_for_student_id)
async def process_student_id_step(message: Message, state: FSMContext):
    student_id = message.text.strip().replace(" ", "").upper()
    data = await state.get_data()
    full_name = data.get("full_name")
    course_code = data.get("enrolling_course_code", "GENERAL")
    telegram_id = message.from_user.id
    
    db.enroll_student(telegram_id, full_name, student_id, course_code)
    await state.clear()
    
    await message.answer(
        "DIRE DAWA UNIVERSITY | STUDENT PORTAL\n"
        "========================================\n"
        f"Student:     {full_name}\n"
        f"Student ID:  {student_id}\n"
        f"Enrolled In: {course_code}\n"
        "Status:      [REGISTERED & ACTIVE]\n"
        "========================================\n"
        "Welcome! Use the official controls below, or type your 4-digit PIN during class:",
        reply_markup=get_student_portal_keyboard()
    )

@dp.callback_query(F.data == "portal_student")
async def show_student_portal(callback: CallbackQuery, state: FSMContext):
    student = db.get_student_by_telegram_id(callback.from_user.id)
    if not student:
        await callback.message.answer(
            "Account Not Found.\n"
            "Please use the registration link provided by your Class Representative (CR)."
        )
        return
        
    stu_id, name, course_code = student
    await callback.message.answer(
        "DIRE DAWA UNIVERSITY | STUDENT PORTAL\n"
        "========================================\n"
        f"Student:     {name}\n"
        f"Student ID:  {stu_id}\n"
        f"Enrolled In: {course_code}\n"
        "========================================\n"
        "Use the official controls below, or type your 4-digit PIN during class:",
        reply_markup=get_student_portal_keyboard()
    )


@dp.callback_query(F.data == "student_checkin")
async def ask_student_pin(callback: CallbackQuery, state: FSMContext):
    await state.set_state(StudentPINEntry.waiting_for_pin)
    await callback.message.answer("Enter the 4-digit Attendance PIN displayed in class:")

@dp.message(StudentPINEntry.waiting_for_pin)
async def verify_student_pin(message: Message, state: FSMContext):
    await state.clear()
    await execute_pin_verification(message, message.text.strip())

@dp.message(F.text.regexp(r"^\d{4}$"))
async def direct_pin_input(message: Message):
    await execute_pin_verification(message, message.text.strip())

async def execute_pin_verification(message: Message, entered_pin: str):
    status, student_id, full_name, course_name = db.verify_and_record_pin(message.from_user.id, entered_pin)
    
    if status == "SUCCESS":
        await message.answer(
            "DIRE DAWA UNIVERSITY | ATTENDANCE VERIFIED\n"
            "========================================\n"
            f"Student:   {full_name} ({student_id})\n"
            f"Course:    {course_name}\n"
            f"Time:      {datetime.now().strftime('%I:%M:%S %p')}\n"
            "Status:    [PRESENT]\n"
            "Method:    PIN Authentication\n"
            "========================================"
        )
    elif status == "ALREADY_PRESENT":
        await message.answer("Notice: You are already marked PRESENT for this session.")
    elif status == "EXPIRED":
        await message.answer(
            "ATTENDANCE CHECK-IN CLOSED\n"
            "----------------------------------------\n"
            "The time window for this PIN has expired."
        )
    elif status == "NOT_ENROLLED_IN_THIS_COURSE":
        await message.answer(
            f"ACCESS DENIED\n"
            f"----------------------------------------\n"
            f"You are not enrolled in {course_name}.\n"
            f"You can only submit attendance for your own registered course."
        )
    elif status == "NOT_ENROLLED":
        await message.answer("Error: You are not enrolled in any course yet. Use the link provided by your Class Rep.")
    else:
        await message.answer("Invalid PIN. Please verify the code displayed by your instructor and try again.")



@dp.callback_query(F.data == "student_leave")
async def ask_leave_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LeaveRequestForm.waiting_for_date)
    await callback.message.answer(
        "Permission / Leave of Absence Request\n"
        "----------------------------------------\n"
        "Enter the Date of Absence (Format: YYYY-MM-DD):"
    )

@dp.message(LeaveRequestForm.waiting_for_date)
async def process_leave_date(message: Message, state: FSMContext):
    await state.update_data(leave_date=message.text.strip())
    await state.set_state(LeaveRequestForm.waiting_for_reason)
    await message.answer("Enter the formal reason for your absence (e.g., Medical Examination, Family Emergency):")

@dp.message(LeaveRequestForm.waiting_for_reason)
async def process_leave_reason(message: Message, state: FSMContext):
    reason = message.text.strip()
    data = await state.get_data()
    leave_date = data.get("leave_date")
    student = db.get_student_by_telegram_id(message.from_user.id)
    
    if not student:
        await state.clear()
        return
        
    stu_id, name, course_code = student
    request_id = db.submit_leave_request(stu_id, name, course_code, leave_date, reason)
    await state.clear()
    
    await message.answer(
        "DIRE DAWA UNIVERSITY | LEAVE REQUEST FILED\n"
        "========================================\n"
        f"Student:   {name} ({stu_id})\n"
        f"Date:      {leave_date}\n"
        f"Reason:    {reason}\n"
        "Status:    [PENDING FACULTY REVIEW]\n"
        "========================================\n"
        "Your request has been dispatched to the course instructor."
    )

async def main():
    db.init_db()
    logging.info("DDU Attendance Management System: Full Enterprise Engine Online.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout
    )
    asyncio.run(main())