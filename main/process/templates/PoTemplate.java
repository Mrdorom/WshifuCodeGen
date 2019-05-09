package {{po_package}};

{% for item in import_info %}import {{item}};
{% endfor %}

/**
 * {{comment}}
 */
@Data
@ToString
@Table(name = "{{meta_data.name}}")
public class {{java_class_name}} {
{% for item in fields %}
    /**
     * {{item.comment}}
     */
{%- if item.annotations %}
{%- for annotation in item.annotations %}
    {{annotation}}
{%- endfor %}
{%- endif %}
    private {{item.java_type}} {{item.name}};
{% endfor %}
}
