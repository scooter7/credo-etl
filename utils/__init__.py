# utils/__init__.py

# File handlers
from .file_handlers import (
    load_excel,
    load_pdf_text,
    analyze_excel_structure,
    detect_bldg_lookup_sheet,
    guess_bldg_column_map,
    load_bldg_room_lookup,
    merge_class_schedule,
)

# Transformations
from .transformations import (
    build_course_schedule,
    build_campus_rooms,
    build_campus_buildings,
    build_academic_departments,   # <-- exact name
    build_rooms_inventory,
    build_course_instructors,
)

# Analysis
from .analysis import (
    calculate_room_utilization,
    summarize_utilization,
    detect_room_conflicts,
    detect_instructor_conflicts,
)

# Reporting
from .reporting import (
    create_full_deliverable,
)
