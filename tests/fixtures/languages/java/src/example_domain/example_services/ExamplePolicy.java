package example_domain.example_services;

import example_domain.example_model.ExampleRecord;

public final class ExamplePolicy {
    public boolean example_allows(ExampleRecord example_record) {
        return !example_record.example_active();
    }
}
