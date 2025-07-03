import pandas as pd

def analyze_all_relationships(csv_path):
    # Load and clean
    df = pd.read_csv(csv_path, dtype=str).fillna('')

    # Define all parent→child relationships
    relationships = [
        ('lean_control_service_id','jira_backlog_id','Lean Control Service','Jira Backlog'),
        ('jira_backlog_id','lean_control_service_id','Jira Backlog','Lean Control Service'),
        ('lean_control_service_id','id','Lean Control Service','Business Service'),
        ('jira_backlog_id','id','Jira Backlog','Business Service'),
        ('id','app_id','Business Service','App'),
        ('lean_control_service_id','app_id','Lean Control Service','App'),
        ('jira_backlog_id','app_id','Jira Backlog','App'),
        ('app_id','instance_id','App','Service Instance'),
        ('id','instance_id','Business Service','Service Instance'),
        ('lean_control_service_id','instance_id','Lean Control Service','Service Instance'),
        ('jira_backlog_id','instance_id','Jira Backlog','Service Instance'),
    ]

    results = []

    for parent_col, child_col, parent_lbl, child_lbl in relationships:
        # Filter to non-empty, distinct pairs
        sub = (
            df[[parent_col, child_col]]
            .query(f"{parent_col} != '' and {child_col} != ''")
            .drop_duplicates()
        )

        # Compute cardinalities
        children_counts = sub.groupby(parent_col)[child_col].nunique()
        parent_counts   = sub.groupby(child_col)[parent_col].nunique()

        max_children = int(children_counts.max()) if not children_counts.empty else 0
        max_parents  = int(parent_counts.max())   if not parent_counts.empty    else 0

        # Classify relationship
        if max_children > 1 and max_parents > 1:
            rel_type = 'many-to-many'
        elif max_children > 1 and max_parents == 1:
            rel_type = 'one-to-many'
        elif max_children == 1 and max_parents == 1:
            rel_type = 'one-to-one'
        else:
            rel_type = 'many-to-one'

        # Sample up to 3 example pairs
        examples = sub.sample(n=min(3, len(sub))) if not sub.empty else sub
        example_list = [f"{p} → {c}" for p, c in examples.values]

        results.append({
            'Relationship':      f"{parent_lbl} → {child_lbl}",
            'Type':              rel_type,
            'Max children/parent': max_children,
            'Max parents/child':  max_parents,
            'Examples':          example_list
        })

    return pd.DataFrame(results)

if __name__ == "__main__":
    summary_df = analyze_all_relationships("tree_edges.csv")
    print(summary_df.to_string(index=False))