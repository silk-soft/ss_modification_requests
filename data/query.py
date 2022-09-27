class QueryList:
    update_attendance_check_in = "UPDATE hr_attendance SET check_in = %s WHERE id = %s"
    update_attendance_check_out = "UPDATE hr_attendance SET check_out = %s WHERE id = %s"
