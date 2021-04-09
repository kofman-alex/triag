truncate rules cascade;

insert into rules (rule_id, rule_priority, summary, expr, msg) values (
    'inactivity',
    1, 
    'User did not enter any activity in the last 24 hours', 
    'select user_id::integer, min_age_by_user.min_age from (select user_id, min(age(now(), time)) as min_age from ${schema}.events group by user_id) min_age_by_user  where min_age_by_user.min_age >= interval ''24 hours''',
    'Hi you still have some activiites to finish, now is the time'
);

insert into rules (rule_id, rule_priority, summary, expr, msg) values (
    'missing-medication',
    2, 
    'The user missed to report his medications 3 days in a row', 
    'select user_id::integer, min_age_by_user.min_age from (select user_id, min(age(now(), time)) as min_age from ${schema}.events where type like ''medication'' group by user_id) min_age_by_user  where min_age_by_user.min_age > interval ''3 days''',
    'Hi, just checking in to see that you take your meds'
);

insert into rules (rule_id, rule_priority, summary, expr, msg) values (
    'pro-deterioration',
    3, 
    'PRO rating is getting higher 3 days in a row', 
    'select user_id, slope from (
        select regr_slope(extract(epoch from time), value) slope, user_id from (
            select to_number(value[1], ''999d99'') as value, user_id, time from (
                select generate_subscripts(value, 1) as s, value, user_id, time from
                (
                    select regexp_matches(description, ''(\d+)\s-\s\w+'') as value, user_id, time from ${schema}.events 
                    where current_timestamp - time < interval ''3 days'' and type=''PRO'' 
                ) as values
            ) as values
        ) as values group by user_id) as values where slope > 0;',
    'Patient''s situation deteriorating'
);

insert into rules (rule_id, rule_priority, summary, expr, msg) values (
    'activity-endorsement',
    4, 
    'The user has more than 5 tasks done at the same day', 
    'select user_id::integer, daily_tasks_by_user.total from (select user_id, count(*) as total from ${schema}.events where age(now(), time) < interval ''1 day'' group by user_id) daily_tasks_by_user where  daily_tasks_by_user.total > 5',
    'What a great day today - keep up the good work'
);