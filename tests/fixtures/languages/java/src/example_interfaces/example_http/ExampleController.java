package example_interfaces.example_http;

import com.google.gson.Gson;
import example_application.example_actions.ExampleAction;
import example_domain.example_model.ExampleRecord;

public final class ExampleController {
    private final ExampleAction example_action;
    private final Gson example_json;

    public ExampleController(ExampleAction example_action, Gson example_json) {
        this.example_action = example_action;
        this.example_json = example_json;
    }

    public String example_handle(String example_id) {
        ExampleRecord example_record = new ExampleRecord(example_id, true);
        return example_json.toJson(example_action.example_execute(example_record));
    }
}
