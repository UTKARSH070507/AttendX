"""
AttendX - Statistical Engine Automated Test Suite
Validates mathematical calculations, hypotheses tests, assumption evaluations, and edge cases.
"""
import pytest
import numpy as np
from services import stats_service

def test_descriptive_stats_accuracy():
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = stats_service.get_descriptive_stats(data)
    assert res['count'] == 5
    assert res['mean'] == 30.0
    assert res['median'] == 30.0
    assert res['min'] == 10.0
    assert res['max'] == 50.0
    assert res['std'] == round(float(np.std(data, ddof=1)), 2)

def test_outlier_detection_iqr():
    # Normal cluster with one extreme high outlier
    data = [45.0, 46.0, 47.0, 48.0, 49.0, 50.0, 51.0, 52.0, 99.0]
    labels = [f"S{i}" for i in range(len(data))]
    outliers = stats_service.detect_outliers_iqr(data, labels)
    assert len(outliers) == 1
    assert outliers[0]['value'] == 99.0
    assert outliers[0]['boundary'] == 'above_upper'

def test_welch_anova_calculation():
    # Groups with clearly different means and unequal variances
    g1 = [20.0, 25.0, 22.0, 28.0]
    g2 = [55.0, 60.0, 58.0, 72.0]
    g3 = [85.0, 95.0, 90.0, 92.0]
    f_stat, df1, df2, pval = stats_service.calculate_welch_anova([g1, g2, g3])
    assert f_stat > 0
    assert df1 == 2
    assert df2 > 0
    assert pval < 0.001

def test_games_howell_posthoc_calculation():
    g1 = [20.0, 25.0, 22.0, 28.0]
    g2 = [55.0, 60.0, 58.0, 72.0]
    g3 = [85.0, 95.0, 90.0, 92.0]
    names = ['Low', 'Med', 'High']
    results = stats_service.calculate_games_howell_posthoc([g1, g2, g3], names)
    assert len(results) == 3
    for comp in results:
        assert 'comparison' in comp
        assert 'p_value' in comp
        assert 'ci_95' in comp
        assert comp['significant'] is True

def test_perform_statistical_analysis_insufficient_data(tmp_path):
    test_db = str(tmp_path / "empty.db")
    from database import init_db, get_db_connection
    conn = get_db_connection(test_db)
    with conn:
        conn.execute("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, 
                attendance_percentage REAL, marks REAL
            )
        """)
        # Insert only 2 records
        conn.execute("INSERT INTO students VALUES (1, 'R1', 'S1', 70.0, 75.0)")
        conn.execute("INSERT INTO students VALUES (2, 'R2', 'S2', 80.0, 85.0)")
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'insufficient_data'
    assert res['sample_size'] == 2

def test_perform_statistical_analysis_constant_values(tmp_path):
    test_db = str(tmp_path / "constant.db")
    from database import get_db_connection
    conn = get_db_connection(test_db)
    with conn:
        conn.execute("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, 
                attendance_percentage REAL, marks REAL
            )
        """)
        # Insert records with constant attendance
        for i in range(5):
            conn.execute(f"INSERT INTO students VALUES ({i}, 'R{i}', 'S{i}', 80.0, {60.0 + i * 5})")
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'constant_variance'

def test_perform_statistical_analysis_full_pipeline(tmp_path):
    test_db = str(tmp_path / "full.db")
    from database import init_db
    init_db(test_db)  # Seeds 30 realistic records

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'success'
    assert res['sample_size'] == 30

    # Pearson assertions
    assert 'pearson' in res
    assert 0.7 < res['pearson']['r'] <= 1.0  # Positive correlation
    assert res['pearson']['significant'] is True
    assert len(res['pearson']['ci_95']) == 2
    assert res['pearson']['ci_95'][0] < res['pearson']['ci_95'][1]

    # Spearman assertions
    assert 'spearman' in res
    assert 0.7 < res['spearman']['rho'] <= 1.0
    assert res['spearman']['significant'] is True

    # Group statistics
    assert 'groups' in res
    assert res['groups']['high']['count'] > 0
    assert res['groups']['medium']['count'] > 0
    assert res['groups']['low']['count'] > 0

    # ANOVA assertions
    assert 'anova' in res
    assert res['anova']['significant'] is True
    assert res['anova']['post_hoc'] is not None
    assert len(res['anova']['post_hoc']['comparisons']) >= 1

def test_statistical_known_negative_association(tmp_path):
    """
    Synthetic dataset with deliberate negative linear association:
    Higher attendance corresponds to lower marks (e.g. inverse scale).
    """
    test_db = str(tmp_path / "neg.db")
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, attendance_percentage REAL, marks REAL)")
    # Synthetic negative correlation: marks = 100 - attendance + noise
    np.random.seed(42)
    att = np.linspace(40, 95, 20)
    marks = 100 - att + np.random.normal(0, 2, 20)
    for i in range(20):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+1, f"NEG-{i}", f"Student {i}", float(att[i]), float(marks[i])))
    conn.commit()
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'success'
    assert res['pearson']['r'] < -0.80
    assert res['pearson']['significant'] is True
    assert "Negative" in res['pearson']['strength']
    assert res['spearman']['rho'] < -0.80

def test_statistical_no_observed_association(tmp_path):
    """
    Synthetic dataset with independent uniform variables: zero true correlation (p >= 0.05).
    """
    test_db = str(tmp_path / "uncorrelated.db")
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, attendance_percentage REAL, marks REAL)")
    # Uncorrelated data
    np.random.seed(123)
    att = np.random.uniform(40, 95, 30)
    marks = np.random.uniform(40, 95, 30)
    for i in range(30):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+1, f"UNC-{i}", f"Student {i}", float(att[i]), float(marks[i])))
    conn.commit()
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'success'
    assert abs(res['pearson']['r']) < 0.35
    assert res['pearson']['significant'] is False
    assert res['pearson']['decision'] == "Fail to reject H0"

def test_statistical_constant_marks(tmp_path):
    """
    Synthetic dataset where all students have identical marks (zero variance in Y).
    """
    test_db = str(tmp_path / "const_marks.db")
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, attendance_percentage REAL, marks REAL)")
    for i in range(10):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+1, f"CM-{i}", f"Student {i}", float(50 + i * 4), 75.0))
    conn.commit()
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'constant_variance'
    assert 'zero variance' in res['message'].lower()

def test_statistical_empty_attendance_groups(tmp_path):
    """
    Synthetic dataset where students only belong to ONE group (e.g. all High >= 80%).
    ANOVA should report insufficient_groups gracefully.
    """
    test_db = str(tmp_path / "one_group.db")
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, attendance_percentage REAL, marks REAL)")
    for i in range(10):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+1, f"HG-{i}", f"High Student {i}", float(85 + i), float(80 + i)))
    conn.commit()
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'success'
    assert res['groups']['high']['count'] == 10
    assert res['groups']['medium']['count'] == 0
    assert res['groups']['low']['count'] == 0
    assert res['anova']['status'] == 'insufficient_groups'

def test_statistical_unequal_variances_welch(tmp_path):
    """
    Synthetic dataset with heteroscedasticity (severely unequal group variances),
    proving that Levene's test detects variance inequality and automatically triggers Welch's ANOVA.
    """
    test_db = str(tmp_path / "unequal_var.db")
    import sqlite3
    conn = sqlite3.connect(test_db)
    conn.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, roll_number TEXT, name TEXT, attendance_percentage REAL, marks REAL)")
    # Low group: tiny variance (std ~ 0.5)
    for i in range(10):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+1, f"LV-{i}", f"Low {i}", 45.0 + i*0.5, 40.0 + (i % 2)*0.5))
    # Medium group: medium variance (std ~ 5)
    for i in range(10):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+11, f"MV-{i}", f"Med {i}", 65.0 + i, 60.0 + (i - 5)*2))
    # High group: massive variance (std ~ 20)
    for i in range(10):
        conn.execute("INSERT INTO students VALUES (?, ?, ?, ?, ?)", (i+21, f"HV-{i}", f"High {i}", 85.0 + i, 50.0 + (i - 5)*8))
    conn.commit()
    conn.close()

    res = stats_service.perform_statistical_analysis(db_path=test_db)
    assert res['status'] == 'success'
    assert res['assumptions']['homogeneity_of_variance']['equal_variances_assumed'] is False
    assert "Welch" in res['anova']['test_name']
    assert "Games-Howell" in res['anova']['post_hoc']['method']


