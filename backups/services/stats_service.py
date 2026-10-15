"""
AttendX - Statistical Analysis Engine
Comprehensive, scientifically rigorous statistical testing module.
Implements:
- Descriptive statistics and Tukey's fences outlier diagnostics
- Pearson correlation with Fisher's z 95% Confidence Intervals
- Spearman rank correlation (linear vs monotonic distinction)
- Attendance tier breakdown (Low <60%, Medium 60-80%, High >=80%)
- Homogeneity of variance (Levene's test) & Normality (Shapiro-Wilk)
- Ordinary One-Way ANOVA vs Welch's ANOVA (unequal variances)
- Pairwise Post-Hoc comparisons: Tukey HSD & Games-Howell
"""
import numpy as np
import pandas as pd
from scipy import stats
from database import get_db_connection

def get_student_dataframe(db_path=None):
    """
    Extracts all valid student records from SQLite into a Pandas DataFrame.
    """
    conn = get_db_connection(db_path)
    try:
        df = pd.read_sql_query(
            """
            SELECT id, roll_number, name, attendance_percentage, marks 
            FROM students 
            WHERE attendance_percentage IS NOT NULL AND marks IS NOT NULL
            """,
            conn
        )
        return df
    finally:
        conn.close()

def categorize_attendance(att):
    """
    Categorizes attendance into project-defined tiers.
    """
    if att < 60.0:
        return 'Low (<60%)'
    elif att < 80.0:
        return 'Medium (60-80%)'
    return 'High (≥80%)'

def get_descriptive_stats(series):
    """
    Computes sample descriptive statistics with ddof=1 for sample standard deviation.
    """
    arr = np.asarray(series, dtype=float)
    n = len(arr)
    if n == 0:
        return None

    sorted_arr = np.sort(arr)
    mean_val = float(np.mean(arr))
    median_val = float(np.median(arr))
    std_val = float(np.std(arr, ddof=1)) if n > 1 else 0.0
    min_val = float(np.min(arr))
    max_val = float(np.max(arr))
    q25 = float(np.percentile(arr, 25))
    q75 = float(np.percentile(arr, 75))
    iqr_val = q75 - q25

    return {
        'count': n,
        'mean': round(mean_val, 2),
        'median': round(median_val, 2),
        'std': round(std_val, 2),
        'min': round(min_val, 2),
        'max': round(max_val, 2),
        'q25': round(q25, 2),
        'q75': round(q75, 2),
        'iqr': round(iqr_val, 2)
    }

def detect_outliers_iqr(series, labels=None):
    """
    Detects potential outliers using Tukey's fences (1.5 * IQR).
    """
    arr = np.asarray(series, dtype=float)
    if len(arr) < 4:
        return []
    
    q25 = np.percentile(arr, 25)
    q75 = np.percentile(arr, 75)
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr

    outliers = []
    for idx, val in enumerate(arr):
        if val < lower_bound or val > upper_bound:
            outliers.append({
                'index': idx,
                'identifier': labels[idx] if labels is not None and idx < len(labels) else str(idx),
                'value': round(float(val), 2),
                'boundary': 'below_lower' if val < lower_bound else 'above_upper',
                'lower_fence': round(float(lower_bound), 2),
                'upper_fence': round(float(upper_bound), 2)
            })
    return outliers

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

def calculate_welch_anova(groups):
    """
    Computes Welch's One-Way ANOVA for unequal group variances (Welch, 1951).
    Returns (f_stat, df1, df2, p_val).
    """
    groups = [np.asarray(g, dtype=float) for g in groups]
    k = len(groups)
    n = np.array([len(g) for g in groups], dtype=float)
    m = np.array([np.mean(g) for g in groups], dtype=float)
    v = np.array([np.var(g, ddof=1) for g in groups], dtype=float)

    # Check for zero variance within groups
    if np.any(v == 0):
        v = np.where(v == 0, 1e-6, v)

    w = n / v
    W = np.sum(w)
    m_prime = np.sum(w * m) / W

    num = np.sum(w * (m - m_prime)**2) / (k - 1)
    lambda_term = np.sum(((1.0 - w / W)**2) / (n - 1))
    den = 1.0 + (2.0 * (k - 2) / (k**2 - 1)) * lambda_term
    f_stat = num / den
    df1 = k - 1
    df2 = (k**2 - 1) / (3.0 * lambda_term) if lambda_term > 0 else 1.0
    pval = 1.0 - stats.f.cdf(f_stat, df1, df2)

    return float(f_stat), int(df1), float(df2), float(pval)

def calculate_games_howell_posthoc(groups, group_names):
    """
    Conducts Games-Howell post-hoc pairwise comparisons for unequal variances.
    Utilizes Welch-Satterthwaite degrees of freedom and the Studentized Range distribution.
    """
    k = len(groups)
    results = []
    for i in range(k):
        for j in range(i + 1, k):
            g1, g2 = np.asarray(groups[i], dtype=float), np.asarray(groups[j], dtype=float)
            n1, n2 = len(g1), len(g2)
            m1, m2 = float(np.mean(g1)), float(np.mean(g2))
            v1, v2 = float(np.var(g1, ddof=1)), float(np.var(g2, ddof=1))
            
            diff = m1 - m2
            se = np.sqrt(v1 / n1 + v2 / n2)
            if se == 0:
                se = 1e-6

            t_val = np.abs(diff) / se
            q_val = np.sqrt(2) * t_val

            df_num = (v1 / n1 + v2 / n2)**2
            df_den = ((v1 / n1)**2 / (n1 - 1)) + ((v2 / n2)**2 / (n2 - 1))
            df = df_num / df_den if df_den > 0 else 1.0

            pval = float(1.0 - stats.studentized_range.cdf(q_val, k, df))

            crit_q = float(stats.studentized_range.ppf(0.95, k, df))
            margin = (crit_q / np.sqrt(2)) * se
            ci_lower = diff - margin
            ci_upper = diff + margin

            results.append({
                'comparison': f"{group_names[i]} vs {group_names[j]}",
                'groupA': group_names[i],
                'groupB': group_names[j],
                'mean_diff': round(float(diff), 2),
                'p_value': round(pval, 5),
                'ci_95': [round(float(ci_lower), 2), round(float(ci_upper), 2)],
                'significant': bool(pval < 0.05)
            })
    return results

def perform_statistical_analysis(db_path=None):
    """
    Executes complete, rigorous statistical testing:
    1. Descriptive Statistics & Outlier Identification
    2. Pearson Product-Moment Correlation (Linear association, 95% CI)
    3. Spearman Rank Correlation (Monotonic association)
    4. Group-wise Breakdown (Low <60%, Medium 60-80%, High >=80%)
    5. Test of Homogeneity of Variances (Levene's test) & Normality (Shapiro-Wilk)
    6. Hypothesis Testing: Ordinary One-Way ANOVA or Welch's ANOVA
    7. Post-Hoc Pairwise Comparisons: Tukey HSD or Games-Howell
    """
    df = get_student_dataframe(db_path)
    n = len(df)

    # Guardrail: Insufficient observations
    if n < 3:
        return {
            'status': 'insufficient_data',
            'sample_size': n,
            'message': f"At least 3 student observations are required for correlation and inference (currently {n} available)."
        }

    att = df['attendance_percentage'].values
    marks = df['marks'].values
    roll_labels = df['roll_number'].values

    # 1. Descriptive Statistics
    desc_att = get_descriptive_stats(att)
    desc_marks = get_descriptive_stats(marks)

    # Outlier Detection
    outliers_att = detect_outliers_iqr(att, roll_labels)
    outliers_marks = detect_outliers_iqr(marks, roll_labels)

    # Constant Variables Guardrail
    var_att = float(np.var(att))
    var_marks = float(np.var(marks))
    if var_att == 0.0 or var_marks == 0.0:
        return {
            'status': 'constant_variance',
            'sample_size': n,
            'descriptive': {'attendance': desc_att, 'marks': desc_marks},
            'message': 'Cannot calculate correlation: attendance or marks exhibit zero variance (all values are constant).'
        }

    # 2. Pearson Correlation
    pearson_res = stats.pearsonr(att, marks)
    r = float(pearson_res.statistic)
    p_val_pearson = float(pearson_res.pvalue)

    # t-statistic and degrees of freedom
    df_pearson = n - 2
    t_stat_pearson = r * np.sqrt(df_pearson / max(1e-9, 1.0 - r**2))

    # 95% Confidence Interval for Pearson r (Fisher's z-transformation)
    try:
        ci = pearson_res.confidence_interval(confidence_level=0.95)
        ci_lower = round(float(ci.low), 3)
        ci_upper = round(float(ci.high), 3)
    except (AttributeError, Exception):
        z = 0.5 * np.log((1 + r) / max(1e-9, 1 - r))
        se_z = 1.0 / np.sqrt(n - 3)
        ci_lower = round(float(np.tanh(z - 1.96 * se_z)), 3)
        ci_upper = round(float(np.tanh(z + 1.96 * se_z)), 3)

    # Correlation Strength Classifier
    abs_r = abs(r)
    if abs_r >= 0.70:
        strength_desc = "Strong"
    elif abs_r >= 0.40:
        strength_desc = "Moderate"
    elif abs_r >= 0.20:
        strength_desc = "Weak"
    else:
        strength_desc = "Negligible"

    dir_desc = "Positive" if r > 0 else "Negative"

    pearson_output = {
        'r': round(r, 4),
        'p_value': round(p_val_pearson, 6),
        't_statistic': round(float(t_stat_pearson), 3),
        'degrees_of_freedom': df_pearson,
        'ci_95': [ci_lower, ci_upper],
        'sample_size': n,
        'alpha': 0.05,
        'significant': bool(p_val_pearson < 0.05),
        'strength': f"{strength_desc} {dir_desc}",
        'null_hypothesis': "H0: The population linear correlation between attendance and marks is zero (rho = 0).",
        'alt_hypothesis': "H1: The population linear correlation between attendance and marks is nonzero (rho != 0).",
        'decision': "Reject H0 in favor of H1" if p_val_pearson < 0.05 else "Fail to reject H0",
        'interpretation': (
            f"There is a statistically significant, {strength_desc.lower()} {dir_desc.lower()} linear correlation "
            f"between student attendance percentage and examination marks (r = {round(r, 3)}, p = {round(p_val_pearson, 4)})."
            if p_val_pearson < 0.05 else
            f"No statistically significant linear correlation was observed between attendance percentage and marks (r = {round(r, 3)}, p = {round(p_val_pearson, 4)})."
        )
    }

    # 3. Spearman Rank Correlation
    spearman_res = stats.spearmanr(att, marks)
    rho = float(spearman_res.statistic)
    p_val_spearman = float(spearman_res.pvalue)

    spearman_output = {
        'rho': round(rho, 4),
        'p_value': round(p_val_spearman, 6),
        'sample_size': n,
        'alpha': 0.05,
        'significant': bool(p_val_spearman < 0.05),
        'comparison_note': (
            "Pearson's r evaluates strictly linear relationships, whereas Spearman's rho evaluates monotonic relationships "
            "based on ranks. Spearman is non-parametric and resilient to mild non-normality or outliers."
        ),
        'interpretation': (
            f"Rank-order correlation confirms a statistically significant monotonic association (rho = {round(rho, 3)}, p = {round(p_val_spearman, 4)})."
            if p_val_spearman < 0.05 else
            f"Monotonic association is not statistically significant (rho = {round(rho, 3)}, p = {round(p_val_spearman, 4)})."
        )
    }

    # 4. Attendance Groups Breakdown
    low_marks = df[df['attendance_percentage'] < 60.0]['marks'].values
    med_marks = df[(df['attendance_percentage'] >= 60.0) & (df['attendance_percentage'] < 80.0)]['marks'].values
    high_marks = df[df['attendance_percentage'] >= 80.0]['marks'].values

    # Normality testing per group (Shapiro-Wilk)
    def test_normality(data):
        if len(data) >= 3:
            s_stat, s_p = stats.shapiro(data)
            return {
                'shapiro_w': round(float(s_stat), 3),
                'p_value': round(float(s_p), 4),
                'normally_distributed': bool(s_p >= 0.05)
            }
        return {'note': f'Insufficient observations for Shapiro-Wilk (n={len(data)} < 3).'}

    groups_data = {
        'low': {
            'label': 'Low (<60%)',
            'count': len(low_marks),
            'percentage': round((len(low_marks) / n) * 100, 1),
            'stats': get_descriptive_stats(low_marks),
            'normality': test_normality(low_marks)
        },
        'medium': {
            'label': 'Medium (60-80%)',
            'count': len(med_marks),
            'percentage': round((len(med_marks) / n) * 100, 1),
            'stats': get_descriptive_stats(med_marks),
            'normality': test_normality(med_marks)
        },
        'high': {
            'label': 'High (≥80%)',
            'count': len(high_marks),
            'percentage': round((len(high_marks) / n) * 100, 1),
            'stats': get_descriptive_stats(high_marks),
            'normality': test_normality(high_marks)
        }
    }

    # 5. Group Comparison: Assumptions & ANOVA
    active_groups = []
    active_names = []
    for grp_data, name in [(low_marks, 'Low (<60%)'), (med_marks, 'Medium (60-80%)'), (high_marks, 'High (≥80%)')]:
        if len(grp_data) >= 2:
            active_groups.append(grp_data)
            active_names.append(name)

    anova_output = None
    assumptions_output = {}

    if len(active_groups) >= 2:
        # Check Homogeneity of Variances via Levene's Test (median-centered Brown-Forsythe)
        levene_stat, levene_p = stats.levene(*active_groups, center='median')
        equal_variances = bool(levene_p >= 0.05)

        assumptions_output['homogeneity_of_variance'] = {
            'test_name': "Levene's Test (median-centered)",
            'statistic': round(float(levene_stat), 3),
            'p_value': round(float(levene_p), 4),
            'equal_variances_assumed': equal_variances,
            'interpretation': (
                "Variances across attendance groups appear homogeneous (p >= 0.05). Ordinary ANOVA is appropriate."
                if equal_variances else
                "Variances across attendance groups differ significantly (p < 0.05, heteroscedasticity). Welch's ANOVA is required."
            )
        }

        # Perform appropriate ANOVA test
        if equal_variances:
            f_stat, anova_p = stats.f_oneway(*active_groups)
            k = len(active_groups)
            df1 = k - 1
            df2 = sum(len(g) for g in active_groups) - k
            test_type = "One-Way ANOVA (Ordinary Fisher's)"
        else:
            f_stat, df1, df2, anova_p = calculate_welch_anova(active_groups)
            test_type = "Welch's ANOVA (Robust to Unequal Variances)"

        significant = bool(anova_p < 0.05)

        # Post-Hoc Pairwise Comparisons if significant
        post_hoc_output = None
        if significant and len(active_groups) >= 2:
            if equal_variances:
                # Tukey HSD
                try:
                    thsd = stats.tukey_hsd(*active_groups)
                    comparisons = []
                    k = len(active_groups)
                    for i in range(k):
                        for j in range(i + 1, k):
                            diff = float(thsd.statistic[i][j])
                            pval = float(thsd.pvalue[i][j])
                            ci = thsd.confidence_interval(0.95)
                            ci_low = float(ci.low[i][j])
                            ci_high = float(ci.high[i][j])
                            comparisons.append({
                                'comparison': f"{active_names[i]} vs {active_names[j]}",
                                'groupA': active_names[i],
                                'groupB': active_names[j],
                                'mean_diff': round(-diff, 2), # Sign relative to A - B
                                'p_value': round(pval, 5),
                                'ci_95': [round(ci_low, 2), round(ci_high, 2)],
                                'significant': bool(pval < 0.05)
                            })
                    post_hoc_output = {
                        'method': 'Tukey HSD (Honest Significant Difference)',
                        'comparisons': comparisons
                    }
                except Exception as e:
                    post_hoc_output = {'error': f"Tukey HSD computation error: {str(e)}"}
            else:
                # Games-Howell for unequal variances
                try:
                    gh_comps = calculate_games_howell_posthoc(active_groups, active_names)
                    post_hoc_output = {
                        'method': "Games-Howell Post-Hoc Test (Unequal Variances)",
                        'comparisons': gh_comps
                    }
                except Exception as e:
                    post_hoc_output = {'error': f"Games-Howell computation error: {str(e)}"}

        anova_output = {
            'test_name': test_type,
            'f_statistic': round(float(f_stat), 3),
            'df1': int(df1),
            'df2': round(float(df2), 2),
            'p_value': round(float(anova_p), 6),
            'alpha': 0.05,
            'significant': significant,
            'null_hypothesis': "H0: Mean examination marks are equal across all attendance tiers (mu_Low = mu_Med = mu_High).",
            'alt_hypothesis': "H1: At least one attendance tier exhibits a statistically distinct mean examination mark.",
            'decision': "Reject H0 in favor of H1" if significant else "Fail to reject H0",
            'interpretation': (
                f"Statistically significant variance in examination marks observed across attendance tiers "
                f"(F({int(df1)}, {round(float(df2), 1)}) = {round(float(f_stat), 2)}, p = {round(float(anova_p), 4)})."
                if significant else
                f"No statistically significant difference in examination marks across attendance tiers "
                f"(F({int(df1)}, {round(float(df2), 1)}) = {round(float(f_stat), 2)}, p = {round(float(anova_p), 4)})."
            ),
            'post_hoc': post_hoc_output
        }
    else:
        anova_output = {
            'status': 'insufficient_groups',
            'message': 'At least two attendance tiers must each contain 2 or more student records to perform ANOVA.'
        }

    return {
        'status': 'success',
        'sample_size': n,
        'research_hypotheses': [
            {
                'question': '1. Is attendance associated with examination marks?',
                'method': 'Pearson product-moment correlation (linear) and Spearman rank correlation (monotonic)',
                'alpha': 0.05
            },
            {
                'question': '2. Do students with different attendance levels show statistically significant differences in marks?',
                'method': 'One-Way ANOVA (or Welch ANOVA if Levene test indicates unequal variances) with Post-Hoc testing',
                'alpha': 0.05
            }
        ],
        'descriptive': {
            'attendance': desc_att,
            'marks': desc_marks
        },
        'data_quality': {
            'outliers': {
                'attendance': outliers_att,
                'marks': outliers_marks
            },
            'diagnostic_note': (
                "Diagnostic checks (Shapiro-Wilk, Levene's) provide empirical evidence regarding test assumptions, "
                "but do not definitively prove that population assumptions are satisfied."
            )
        },
        'pearson': pearson_output,
        'spearman': spearman_output,
        'groups': groups_data,
        'assumptions': assumptions_output,
        'anova': anova_output,
        'methodological_guidelines': {
            'association_vs_causation': (
                "Association does not equal causation: A statistically significant correlation or ANOVA difference "
                "proves co-variation between attendance and examination performance, but does not prove attendance causes higher marks. "
                "Confounding variables (prior knowledge, study discipline, interest) are also influential."
            ),
            'practical_vs_statistical_significance': (
                "Statistical significance indicates that observed differences are unlikely to be due to chance sampling error alone, "
                "while effect size (r = " + str(round(r, 2)) + ") quantifies the practical magnitude of the association."
            )
        }
    }
