import random
import datetime

class StudyPlanGenerator:
    def __init__(self, courses, daily_routine, total_days, semester_start_date):
        """
        Initialize with the user's input:
        courses: list of tuples (course_name, units)
        daily_routine: daily available study time in hours
        total_days: total number of days in the semester
        semester_start_date: starting date of the semester (as a string)
        """
        self.courses = courses
        self.daily_routine = daily_routine
        self.total_days = total_days
        self.semester_start_date = datetime.datetime.strptime(semester_start_date, "%Y-%m-%d")
        self.schedule = []

    def distribute_study_time(self):
        """Distribute study time across courses based on units (weight)."""
        total_units = sum([course[1] for course in self.courses])
        daily_study_hours = self.daily_routine

        course_schedule = []
        
        for course, units in self.courses:
            # Calculate the proportion of study time based on units
            study_time_per_course = (units / total_units) * daily_study_hours
            study_time_per_course = round(study_time_per_course, 2)  # round to 2 decimal places
            course_schedule.append((course, study_time_per_course))
        
        return course_schedule

    def generate_study_plan(self):
        """Generate a study plan by assigning courses to each day."""
        course_schedule = self.distribute_study_time()
        days = []
        
        # Start generating the study schedule
        for i in range(self.total_days):
            date = self.semester_start_date + datetime.timedelta(days=i)
            day_courses = random.sample(course_schedule, len(course_schedule))  # Shuffle courses for variety

            daily_plan = f"Date: {date.strftime('%Y-%m-%d')}\n"
            daily_plan += f"Study Time Available: {self.daily_routine} hours\n"
            
            for course, study_time in day_courses:
                daily_plan += f"{course}: {study_time} hours\n"

            days.append(daily_plan)

        self.schedule = days

    def save_to_file(self, filename="study_plan.txt"):
        """Save the generated study plan to a text file."""
        with open(filename, "w") as file:
            file.write("### Study Plan ###\n\n")
            for day in self.schedule:
                file.write(day)
                file.write("\n====================\n")

    def print_schedule(self):
        """Print the generated study schedule to the console."""
        print("### Study Plan ###\n")
        for day in self.schedule:
            print(day)
            print("====================")

def get_courses_from_user(num_courses):
    """Ask the user to input their courses and units."""
    courses = []
    for _ in range(num_courses):
        course_name = input("Enter course name: ").strip()
        try:
            units = int(input(f"Enter the number of units for {course_name}: ").strip())
            courses.append((course_name, units))
        except ValueError:
            print("Please enter a valid number of units.")
    return courses

def main():
    # Ask if the user is studying engineering
    is_engineering = input("Are you studying engineering? (yes/no): ").strip().lower()
    if is_engineering != "yes":
        print("Sorry, this service is only for engineering students.")
        return

    # Ask the user for the number of courses in the semester
    try:
        num_courses = int(input("How many courses do you have in the semester? ").strip())
        if num_courses <= 0:
            print("You need to have at least one course.")
            return
    except ValueError:
        print("Please enter a valid number for courses.")
        return

    # Get the courses and their units
    courses = get_courses_from_user(num_courses)
    
    # Input: daily study routine, number of available study days in the semester, and start date of semester
    try:
        daily_routine = float(input("Enter the number of hours you can study per day: ").strip())
        total_days = int(input("Enter the total number of days in your semester: ").strip())
        semester_start_date = input("Enter the semester start date (YYYY-MM-DD): ").strip()
        
        # Check the format of the date input
        try:
            datetime.datetime.strptime(semester_start_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
            return
    except ValueError:
        print("Invalid input. Please make sure you enter numeric values where appropriate.")
        return

    # Initialize StudyPlanGenerator
    study_plan_generator = StudyPlanGenerator(courses, daily_routine, total_days, semester_start_date)
    
    # Generate the study plan
    study_plan_generator.generate_study_plan()
    
    # Save the schedule to a text file
    study_plan_generator.save_to_file("study-plan-generator.txt")
    
    # Print the schedule to the console (optional)
    study_plan_generator.print_schedule()

if __name__ == "__main__":
    main()
