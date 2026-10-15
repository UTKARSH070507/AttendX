"""
AttendX - Statistical Analysis Engine
Calculates descriptive statistics, Pearson/Spearman correlations, and ANOVA using Pandas, NumPy, and SciPy.
"""
import numpy as np
import pandas as pd
from scipy import stats
from database import get_db_connection

def get_student_dataframe(db_path=None):
    """
    Extracts all student records from SQLite into a Pandas DataFrame.
    """
    conn = get_db_connection(db_path)
    try:
        df = pd.read_sql_query(
            "SELECT id, roll_number, name, attendance_percentage, marks FROM students",
            conn
        )
        return df
    finally:
        conn.close()

def categorize_attendance(att):
    if att < 60.0:
        return 'Low (<60%)'
    elif att < 80.0:
        return 'Medium (60-80%)'
    return 'High (≥80%)'

def calculate_dashboard_metrics(db_path=None):
    """
    Computes key summary indicators and scatter plot coordinates for the dashboard.
    """
    df = get_student_dataframe(db_path)
    n = len(df)

    if n == 0:
        return {
            'total_students': 0,
            'avg_attendance': 0.0,
            'avg_marks': 0.0,
            'groups': {'high': 0, 'medium': 0, 'low': 0},
            'scatter_points': [],
            'group_averages': [
                {'group': 'Low (<60%)', 'avg_marks': 0.0, 'count': 0},
                {'group': 'Medium (60-80%)', 'avg_marks': 0.0, 'count': 0},
                {'group': 'High (≥80%)', 'avg_marks': 0.0, 'count': 0}
            ]
        }

    avg_att = round(float(df['attendance_percentage'].mean()), 2)
    avg_marks = round(float(df['marks'].mean()), 2)

    df['group'] = df['attendance_percentage'].apply(categorize_attendance)

    low_df = df[df['attendance_percentage'] < 60.0]
    med_df = df[(df['attendance_percentage'] >= 60.0) & (df['attendance_percentage'] < 80.0)]
    high_df = df[df['attendance_percentage'] >= 80.0]

    group_counts = {
        'high': len(high_df),
        'medium': len(med_df),
        'low': len(low_df)
    }

    group_averages = [
        {
            'group': 'Low (<60%)',
            'avg_marks': round(float(low_df['marks'].mean()), 2) if len(low_df) > 0 else 0.0,
            'count': len(low_df)
        },
        {
            'group': 'Medium (60-80%)',
            'avg_marks': round(float(med_df['marks'].mean()), 2) if len(med_df) > 0 else 0.0,
            'count': len(med_df)
        },
        {
            'group': 'High (≥80%)',
            'avg_marks': round(float(high_df['marks'].mean()), 2) if len(high_df) > 0 else 0.0,
            'count': len(high_df)
        }
    ]

    scatter_points = [
        {
            'x': round(float(row['attendance_percentage']), 2),
            'y': round(float(row['marks']), 2),
            'roll_number': row['roll_number'],
            'name': row['name'],
            'group': row['group']
        }
        for _, row in df.iterrows()
    ]

    return {
        'total_students': n,
        'avg_attendance': avg_att,
        'avg_marks': avg_marks,
        'groups': group_counts,
        'group_averages': group_averages,
        'scatter_points': scatter_points
    }

def perform_statistical_analysis(db_path=None):
    """
    Executes full statistical procedures:
    - Descriptive stats (attendance & marks)
    - Pearson correlation with 95% CI
    - Spearman rank correlation
    - Group-wise statistics
    - One-way ANOVA
    """
    df = get_student_dataframe(db_path)
    n = len(df)

    if n < 3:
        return {
            'status': 'insufficient_data',
            'sample_size': n,
            'message': 'At least 3 student observations are required to conduct statistical analysis.'
        }

    att = df['attendance_percentage'].values
    marks = df['marks'].values

    # 1. Descriptive Statistics
    def get_desc(series):
        return {
            'mean': round(float(np.mean(series)), 2),
            'median': round(float(np.median(series)), 2),
            'std': round(float(np.std(series, ddof=1)), 2) if len(series) > 1 else 0.0,
            'min': round(float(np.min(series)), 2),
            'max': round(float(np.max(series)), 2)
        }

    descriptive = {
        'attendance': get_desc(att),
        'marks': get_desc(marks),
        'sample_size': n
    }

    # Check for zero variance / constant array
    constant_att = np.all(att == att[0])
    constant_marks = np.all(marks == marks[0])

    if constant_att or constant_marks:
        return {
            'status': 'constant_variance',
            'descriptive': descriptive,
            'message': 'Cannot compute correlation: attendance or marks have zero variance (constant values).'
        }

    # 2. Pearson Correlation
    pearson_res = stats.pearsonr(att, marks)
    r = float(pearson_res.statistic)
    p_val_pearson = float(pearson_res.pvalue)

    # 95% Confidence Interval for Pearson r (Fisher z-transform)
    try:
        ci = pearson_res.confidence_interval(confidence_level=0.95)
        ci_lower = round(float(ci.low), 3)
        ci_upper = round(float(ci.high), 3)
    except AttributeError:
        # Fallback manual Fisher Z calculation for older scipy
        z = 0.5 * np.log((1 + r) / (1 - r))
        se = 1.0 / np.sqrt(n - 3)
        ci_lower = round(float(np.tanh(z - 1.96 * se)), 3)
        ci_upper = round(float(np.tanh(z + 1.96 * se)), 3)

    # 3. Spearman Rank Correlation
    spearman_res = stats.spearmanr(att, marks)
    rho = float(spearman_res.statistic)
    p_val_spearman = float(spearman_res.pvalue)

    # 4. Attendance Groups Breakdown
    low_marks = df[df['attendance_percentage'] < 60.0]['marks'].values
    med_marks = df[(df['attendance_percentage'] >= 60.0) & (df['attendance_percentage'] < 80.0)]['marks'].values
    high_marks = df[df['attendance_percentage'] >= 80.0]['marks'].values

    group_stats = {
        'low': {
            'label': 'Low (<60%)',
            'count': len(low_marks),
            'stats': get_desc(low_marks) if len(low_marks) > 0 else None
        },
        'medium': {
            'label': 'Medium (60-80%)',
            'count': len(med_marks),
            'stats': get_desc(med_marks) if len(med_marks) > 0 else None
        },
        'high': {
            'label': 'High (≥80%)',
            'count': len(high_marks),
            'stats': get_desc(high_marks) if len(high_marks) > 0 else None
        }
    }

    # 5. Group Comparison (One-Way ANOVA)
    valid_groups = [g for g in [low_marks, med_marks, high_marks] if len(g) >= 2]
    anova_res = None
    if len(valid_groups) >= 2:
        try:
            f_stat, anova_p = stats.f_oneway(*valid_groups)
            anova_res = {
                'f_statistic': round(float(f_stat), 3),
                'p_value': float(anova_p),
                'significant': bool(anova_p < 0.05),
                'interpretation': (
                    "Statistically significant difference in marks across attendance groups (p < 0.05)."
                    if anova_p < 0.05 else
                    "No statistically significant difference in marks detected across attendance groups (p >= 0.05)."
                )
            }
        except Exception as e:
            anova_res = {'error': f"ANOVA calculation failed: {str(e)}"}
    else:
        anova_res = {
            'status': 'insufficient_group_data',
            'message': 'At least two attendance tiers must contain 2 or more student records to run ANOVA.'
        }

    return {
        'status': 'success',
        'sample_size': n,
        'descriptive': descriptive,
        'pearson': {
            'r': round(r, 3),
            'p_value': p_val_pearson,
            'ci_95': [ci_lower, ci_upper],
            'significant': bool(p_val_pearson < 0.05),
            'interpretation': (
                f"{'Strong positive' if r > 0.7 else 'Moderate positive' if r > 0.3 else 'Weak'} linear association "
                f"between attendance percentage and examination marks."
            )
        },
        'spearman': {
            'rho': round(rho, 3),
            'p_value': p_val_spearman,
            'significant': bool(p_val_spearman < 0.05),
            'interpretation': "Evaluates monotonic relationship without assuming normal distribution."
        },
        'groups': group_stats,
        'anova': anova_res
    }

