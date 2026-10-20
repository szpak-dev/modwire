package example_application.example_actions;

import example_domain.example_model.ExampleRecord;
import example_domain.example_services.ExamplePolicy;
import java.util.Map;

public final class ExampleAction {
    private final ExamplePolicy example_policy;

    public ExampleAction(ExamplePolicy example_policy) {
        this.example_policy = example_policy;
    }

    public Map<String, String> example_execute(ExampleRecord example_record) {
        if (!example_policy.example_allows(example_record)) {
            return Map.of("example_status", "example_blocked");
        }
        return Map.of("example_status", "example_complete", "example_id", example_record.example_id());
    }
}
