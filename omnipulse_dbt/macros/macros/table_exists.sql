{% macro table_exists(schema, table) %}
  {% set query %}
    SELECT COUNT(*) 
    FROM information_schema.tables
    WHERE table_schema = '{{ schema }}'
    AND table_name = '{{ table }}'
  {% endset %}
  
  {% set results = run_query(query) %}
  {% if execute %}
    {% set exists = results.columns[0].values()[0] > 0 %}
    {{ return(exists) }}
  {% else %}
    {{ return(false) }}
  {% endif %}
{% endmacro %}