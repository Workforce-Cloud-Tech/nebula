/*
 * Copyright (c) 2026. RecruitCRM
 * All rights reserved.
 */

package ${package};

import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * Spring Boot {@code AutoConfiguration} entry point for this library.
 *
 * <p>Listed in {@code META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports}
 * so that any consuming Spring Boot application picks up this package's
 * components, JPA entities, and repositories automatically once the jar is on
 * the classpath.
 */
@ComponentScan(basePackages = { "${package}" })
@EntityScan(basePackages = { "${package}" })
@EnableJpaRepositories(basePackages = { "${package}" })
@Configuration
public class ${packageName}AutoConfiguration {

}
