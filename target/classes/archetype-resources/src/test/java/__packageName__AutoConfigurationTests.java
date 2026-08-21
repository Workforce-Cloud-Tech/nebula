package ${package};

import static org.assertj.core.api.Assertions.assertThat;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import org.springframework.boot.persistence.autoconfigure.EntityScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;

/**
 * Tests for {@link ${packageName}AutoConfiguration}.
 */
@DisplayName("${packageName}AutoConfiguration")
class ${packageName}AutoConfigurationTests {

    @Test
    @DisplayName("Should be a Spring configuration with expected annotations")
    void shouldBeConfiguration() {
        assertThat(${packageName}AutoConfiguration.class.getAnnotations())
                .anyMatch((a) -> a.annotationType().equals(Configuration.class));
        assertThat(${packageName}AutoConfiguration.class.getAnnotations())
                .anyMatch((a) -> a.annotationType().equals(EntityScan.class));
        assertThat(${packageName}AutoConfiguration.class.getAnnotations())
                .anyMatch((a) -> a.annotationType().equals(EnableJpaRepositories.class));
    }

}
