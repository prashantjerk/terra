package edu.lynchburg.terra;

import org.junit.jupiter.api.Test;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import static org.junit.jupiter.api.Assertions.*;

class SchemaUpgradeTests {
    @Test void upgradesOldSpaceTableWithoutLosingRowsAndCanRunTwice() {
        var dataSource = new DriverManagerDataSource(
            "jdbc:h2:mem:upgrade;MODE=PostgreSQL;DB_CLOSE_DELAY=-1", "sa", "");
        var jdbc = new JdbcTemplate(dataSource);
        jdbc.execute("CREATE TABLE parking_spaces (space_id VARCHAR(10) PRIMARY KEY, " +
            "is_occupied BOOLEAN NOT NULL DEFAULT FALSE, last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP)");
        jdbc.execute("INSERT INTO parking_spaces(space_id,is_occupied) VALUES ('A1',TRUE)");
        var script = new ResourceDatabasePopulator(new ClassPathResource("db/schema.sql"));
        script.execute(dataSource);
        script.execute(dataSource);
        assertEquals("A1", jdbc.queryForObject("SELECT label FROM parking_spaces WHERE space_id='A1'", String.class));
        assertTrue(jdbc.queryForObject("SELECT is_occupied FROM parking_spaces WHERE space_id='A1'", Boolean.class));
        assertEquals(0, jdbc.queryForObject("SELECT version FROM parking_spaces WHERE space_id='A1'", Integer.class));
        jdbc.execute("INSERT INTO parking_spaces(space_id,label,is_occupied,last_updated) " +
            "VALUES ('NEW_SPACE_WITH_LONG_ID','New',NULL,CURRENT_TIMESTAMP)");
        assertEquals(2, jdbc.queryForObject("SELECT COUNT(*) FROM parking_spaces", Integer.class));
        assertEquals(0, jdbc.queryForObject("SELECT COUNT(*) FROM parking_logs", Integer.class));
    }
}
