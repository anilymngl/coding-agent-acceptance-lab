CREATE TABLE attempts (
          attempt_id text primary key,
          scenario_id text not null,
          pack text not null,
          system_id text not null,
          model text not null,
          provider text not null,
          route text not null,
          prompt_lane text not null,
          attempt_index integer not null,
          experiment_id text not null,
          planned integer not null,
          retained integer not null,
          exclusion_reason text not null,
          public_pass integer not null,
          hidden_pass integer not null,
          false_green integer not null,
          duration_seconds real not null,
          patch_sha256 text not null,
          source_id text not null,
          started_at text not null
        );

CREATE TABLE cells (
          scenario_id text not null,
          pack text not null,
          system_id text not null,
          prompt_lane text not null,
          planned_attempts integer not null,
          retained_attempts integer not null,
          public_passes integer not null,
          hidden_passes integer not null,
          false_greens integer not null,
          any_hidden_pass integer not null,
          all_retained_hidden_pass integer not null,
          cell_status text not null,
          primary key (scenario_id, system_id, prompt_lane)
        );

CREATE TABLE exclusions (
          attempt_id text primary key,
          scenario_id text not null,
          system_id text not null,
          prompt_lane text not null,
          attempt_index integer not null,
          reason text not null,
          source_id text not null,
          audit_note text not null
        );

CREATE TABLE release_metadata (
          release_id text not null,
          release_date text not null,
          git_commit text not null,
          schema_version text not null,
          study_name text not null,
          description text not null
        );

CREATE TABLE scenarios (
          scenario_id text primary key,
          pack text not null,
          category text not null,
          difficulty text not null,
          description text not null,
          representative integer not null,
          contract_sha256 text not null,
          hidden_test_sha256 text not null
        );

CREATE TABLE source_databases (
          source_id text primary key,
          source_label text not null,
          sha256 text not null,
          schema_version integer not null,
          original_row_count integer not null,
          included_row_count integer not null,
          experiment_ids text not null,
          system_notes text not null,
          route_notes text not null
        );
