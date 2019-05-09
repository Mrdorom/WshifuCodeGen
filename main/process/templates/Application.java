package com.wanshifu;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.builder.SpringApplicationBuilder;
import org.springframework.boot.web.support.SpringBootServletInitializer;
import org.springframework.cloud.netflix.feign.EnableFeignClients;
import org.springframework.transaction.annotation.EnableTransactionManagement;

@SpringBootApplication
{%- if dao_package %}
@MapperScan("{{dao_package}}")
{%- endif %}
@EnableTransactionManagement
@EnableFeignClients
public class {{app_class_name}}Application extends SpringBootServletInitializer {

    @Override
    protected SpringApplicationBuilder configure(
            SpringApplicationBuilder application) {
        return application.sources({{app_class_name}}Application.class);
    }

    public static void main(String[] args) {
        SpringApplication.run({{app_class_name}}Application.class, args);
    }
}

