# Data Generation Approach - Making Data "Make Sense"

**Based on analysis of brighthive-mock-data repository**

## Core Principles

The brighthive-mock-data repo demonstrates sophisticated patterns for generating realistic synthetic data that maintains business logic and relationships. Here's their approach:

---

## 1. Use Faker Library for Base Realism

```python
from faker import Faker
fake = Faker()
Faker.seed(12345)  # For reproducibility

# Realistic names, companies, dates
customer_name = fake.company()
sales_rep = fake.name()
close_date = fake.date_between(start_date="-1y", end_date="today")
```

**Key Benefits:**
- Real-looking names, addresses, emails
- Proper date distributions
- Reproducible with seeds

---

## 2. Weighted Probability Distributions

**Don't use uniform random** - use realistic weights:

```python
# B2B Seasonality: Q4 heavy, summer lighter
month_weights = np.array([1.05, 1.00, 1.10, 0.95, 0.90, 0.85,
                          0.80, 0.88, 1.05, 1.15, 1.20, 1.25])
month_weights = month_weights / month_weights.sum()

# Brand distribution (not equal)
brands = ['Brand_A', 'Brand_B', 'Brand_C']
brand_weights = np.array([0.50, 0.35, 0.15])

# Deal types
deal_types = ['New Business', 'Renewal', 'Upsell', 'Cross-sell']
deal_type_weights = np.array([0.45, 0.30, 0.15, 0.10])
```

**Apply everywhere:**
- Time distributions (seasonality)
- Categorical values (types, sources, regions)
- Outcomes (97% completion, 3% drop rate)

---

## 3. Multi-Factor Correlations

Values should depend on multiple realistic factors:

```python
def calculate_deal_amount(deal_type, brand, enrollment_type, month):
    # Base amount varies by deal type
    if deal_type == 'New Business':
        base = rng.normal(45000, 12000)
    elif deal_type == 'Renewal':
        base = rng.normal(38000, 10000)
    elif deal_type == 'Upsell':
        base = rng.normal(28000, 8000)
    else:  # Cross-sell
        base = rng.normal(22000, 6000)

    # Brand adjustment
    if brand == 'Brand_A':
        base *= 1.2
    elif brand == 'Brand_C':
        base *= 0.8

    # Enrollment type adjustment
    if enrollment_type == 'In-Person':
        base *= 1.15
    elif enrollment_type == 'Online':
        base *= 0.95

    # Q4 deals larger
    if month in [10, 11, 12]:
        base *= 1.08

    return max(5000, base)
```

**Pattern:**
- Start with base value from distribution
- Apply multiplicative adjustments
- Each factor has realistic impact
- Use normal distributions for variation

---

## 4. Temporal Progression & Stage Logic

**Stage transitions with realistic delays:**

```python
def calculate_days_between_stages():
    return {
        'appointment_to_qualified': max(0, int(rng.normal(3, 2))),
        'qualified_to_presentation': max(0, int(rng.normal(7, 3))),
        'presentation_to_decision': max(0, int(rng.normal(10, 5))),
        'decision_to_contract': max(0, int(rng.normal(5, 3))),
        'contract_to_closed': max(0, int(rng.normal(8, 4)))
    }

# Build dates progressively
stage_days = calculate_days_between_stages()
appt_date = create_dt + timedelta(days=rng.integers(0, 3))
qual_date = appt_date + timedelta(days=stage_days['appointment_to_qualified'])
pres_date = qual_date + timedelta(days=stage_days['qualified_to_presentation'])

# Only set dates if stage was reached
appointment_dates.append(appt_date if stage_idx >= 0 else None)
qualified_dates.append(qual_date if stage_idx >= 1 else None)
presentation_dates.append(pres_date if stage_idx >= 2 else None)
```

**Key Patterns:**
- Each stage builds on previous
- Realistic time delays (normal distributions)
- Nulls for unreached stages
- Dates are logically ordered

---

## 5. Relational Integrity & Business Rules

**Student enrollment example:**

```python
def generate_enrollments(students_df, courses_df):
    for _, student in students_df.iterrows():
        # Get courses for student's major
        major_courses = courses_df[courses_df['major'] == student['major']]

        # Take core courses first, then electives
        available_core = major_courses[
            (major_courses['year_level'] == year_level) &
            (~major_courses['course_id'].isin(core_courses_taken))
        ]

        # Business rule: exactly 2 courses per semester
        if len(available_core) >= 2:
            semester_courses = available_core.sample(n=2)
        elif len(available_core) == 1:
            # One core + one elective
            core_course = available_core.sample(n=1)
            elective = electives.sample(n=1)
            semester_courses = pd.concat([core_course, elective])
```

**Patterns:**
- Enforce foreign keys (student_id → enrollments → performance)
- Business rules (2 courses/semester, core before electives)
- Year progression (freshman → sophomore → junior)
- Realistic completion rates (97% complete, 3% drop)

---

## 6. Correlated Attributes

**Performance correlates with status:**

```python
if enrollment['status'] == 'Dropped':
    grade_point = 0.0
    letter_grade = 'F'
    attendance_rate = round(random.uniform(0.0, 0.5), 2)  # Low attendance

elif enrollment['status'] == 'In Progress':
    grade_point = 0.0
    letter_grade = 'IP'
    attendance_rate = round(random.uniform(0.8, 1.0), 2)  # Good attendance

else:  # Completed
    grade_point = random.uniform(2.0, 4.0)
    letter_grade = grade_to_letter(grade_point)
    attendance_rate = round(random.uniform(0.8, 1.0), 2)  # Good attendance
```

**Pattern:**
- Related fields move together
- Dropped → low attendance, F grade
- In Progress → good attendance, no grade yet
- Completed → good attendance, varied grades

---

## 7. Semantic Naming & Codes

**Meaningful identifiers:**

```python
# Course codes reflect major and level
major_codes = {
    'Computer Science': 'CSC',
    'Business': 'BUS',
    'Engineering': 'ENG'
}

# Year-based numbering
for year in [1, 2, 3]:
    base_number = year * 100  # 100, 200, 300
    course_id = f'{code}{base_number + course_num}'  # CSC101, CSC201, CSC301

# Semester codes
semester_code = '01' if semester == 'Fall' else '02'
semester_name = f'{year}-{semester_code}'  # 2024-01, 2024-02
```

**Pattern:**
- Codes convey meaning (CSC = Computer Science)
- Numbers show progression (101 → 201 → 301)
- Formats match industry standards

---

## 8. Data Validation

**Explicit validation functions:**

```python
def validate_data(students_df, courses_df, enrollments_df, performance_df):
    # Check for duplicate IDs
    if students_df['student_id'].duplicated().any():
        raise DataValidationError("Duplicate student IDs found")

    # Check foreign key relationships
    student_ids = set(students_df['student_id'])
    if not set(enrollments_df['student_id']).issubset(student_ids):
        raise DataValidationError("Invalid student IDs in enrollments")

    # Check value ranges
    if not (0 <= performance_df['attendance_rate'].max() <= 1.0):
        raise DataValidationError("Invalid attendance rate values")

    # Check referential integrity
    course_ids = set(courses_df['course_id'])
    if not set(enrollments_df['course_id']).issubset(course_ids):
        raise DataValidationError("Invalid course IDs in enrollments")
```

**Validate:**
- No duplicate primary keys
- Foreign keys reference valid records
- Values within realistic ranges
- Nulls only where appropriate

---

## 9. Hierarchical Data Generation

**Generate in dependency order:**

```python
# 1. Generate dimension tables first
students_df = generate_student_data()
courses_df = generate_courses()

# 2. Generate fact tables that reference dimensions
enrollments_df = generate_enrollments(students_df, courses_df)

# 3. Generate dependent facts
performance_df = generate_academic_performance(enrollments_df)

# 4. Validate all relationships
validate_data(students_df, courses_df, enrollments_df, performance_df)

# 5. Save in order
students_df.to_csv('students.csv')
courses_df.to_csv('courses.csv')
enrollments_df.to_csv('enrollments.csv')
performance_df.to_csv('performance.csv')
```

**Pattern:**
- Dimensions before facts
- Parent tables before child tables
- Validate after generation
- Maintain referential integrity

---

## 10. Conditional Nulls & Optional Fields

**Only populate fields when applicable:**

```python
# Close date only for closed deals
if is_closed:
    days_to_close = max(1, int(rng.normal(45, 20)))
    close_date = create_dt + timedelta(days=days_to_close)

    if is_won:
        closed_won_reason = rng.choice(closed_won_reasons)
        closed_lost_reason = None
    else:
        closed_won_reason = None
        closed_lost_reason = rng.choice(closed_lost_reasons)
else:
    close_date = None
    days_to_close = None
    closed_won_reason = None
    closed_lost_reason = None
```

**Pattern:**
- Nulls represent "not applicable"
- Mutually exclusive fields (won_reason XOR lost_reason)
- Conditional fields (close_date only if closed)

---

## Application to BrightAgent LOADSTRESS

### For Redshift Warehouse Data (1B records):

1. **Define realistic distributions:**
   - Data sources: weighted by common enterprise sources
   - Table types: fact tables (70%), dimension tables (25%), staging (5%)
   - Row counts: log-normal distribution (few huge tables, many small)

2. **Create relationships:**
   - Foreign keys reference valid dimension records
   - Join paths that make business sense
   - Realistic cardinalities (1:many, many:many with bridge tables)

3. **Time-based patterns:**
   - Timestamps with realistic distributions (business hours weighted)
   - Created/modified dates in logical order
   - Seasonal patterns for business data

4. **Schema evolution:**
   - Version numbers for schema changes
   - Backward-compatible additions
   - Realistic column additions over time

5. **Data quality issues:**
   - 95% clean, 5% with realistic issues
   - Missing values in optional fields
   - Occasional duplicates or inconsistencies
   - Outliers within plausible ranges

### For Multi-Source Conflicts (Scenario S02):

1. **Generate 3 sources with overlaps:**
   - Source A: 60% unique, 40% overlap
   - Source B: 50% unique, 50% overlap
   - Source C: 70% unique, 30% overlap

2. **Conflict types:**
   - Same entity, different values (weighted: name variants 40%, measure differences 30%, date conflicts 20%, other 10%)
   - Timestamp-based resolution opportunities
   - Merge strategies (latest, highest quality, business rules)

3. **Realistic variations:**
   - Name: "John Smith" vs "J. Smith" vs "Smith, John"
   - Amounts: $1,234.56 vs $1234.56 vs 1234.56
   - Dates: ISO vs US vs EU formats
   - Missing: NULL vs empty string vs "N/A"

---

## Tools & Libraries

```python
import numpy as np           # For distributions and random
import pandas as pd          # For DataFrames
from faker import Faker      # For realistic fake data
from datetime import datetime, timedelta
import logging              # For monitoring generation

# Set seeds for reproducibility
np.random.seed(42)
Faker.seed(12345)
```

---

## Best Practices Summary

✅ **DO:**
- Use Faker for names, addresses, dates
- Apply weighted distributions everywhere
- Build temporal progressions logically
- Validate foreign keys and constraints
- Use normal distributions for continuous values
- Make correlations match business reality
- Generate dimensions before facts
- Use meaningful codes and identifiers

❌ **DON'T:**
- Use uniform random for everything
- Generate independent random values
- Ignore temporal ordering
- Skip validation
- Use unrealistic value ranges
- Create orphan records
- Generate data without business logic

---

**Next Steps for LOADSTRESS:**

1. Adapt these patterns to warehouse/data lake scenarios
2. Create multi-source generators with realistic conflicts
3. Build schema evolution over time
4. Generate realistic query patterns based on data
5. Validate all relationships before loading to Redshift
