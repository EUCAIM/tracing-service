

CREATE TABLE IF NOT EXISTS DATASETS_V2 (
    id UUID,
    trace_version INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    caller_id VARCHAR NOT NULL,
    user_id VARCHAR NOT NULL,
    user_action VARCHAR NOT NULL,
    dataset_id VARCHAR NOT NULL,
    dataset_group_id UUID NOT NULL,
    update_details VARCHAR,
    use_tool_name VARCHAR,
    use_tool_version VARCHAR,
    create_resources VARCHAR,
    PRIMARY KEY (id)
)
