import datetime

from QuickServeModuleLibrary.forms.datatypes import String
from QuickServeModuleLibrary.forms.forms import QSForm


from QuickServeModuleLibrary.forms.datatypes import (
    String,
    Checkbox,
    Color,
    Email,
    File,
    Number,
    Password,
    Radio,
    RadioSelector,
    Range,
    URL,
    Reset,
    Date,
    Time,
    DateTime,
    Hidden,
    Button,
    SubmitButton,
    Textarea,
)


class BanPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    playerName = String(placeholder="Player Name", required=True)
    banReason = String(placeholder="Ban Reason", required=False)


class BanIp(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    ip = String(placeholder="IP Address", required=True)
    banReason = String(placeholder="Ban Reason", required=False)


class UnBanPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    playerName = String(placeholder="Player Name", required=True)


class UnBanIP(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    ip = String(placeholder="IP Address", required=True)


class OpPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class DeOpPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class WhitelistPlayer(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class WhitelistRemove(QSForm):
    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(action_name, instance_uuid)

    username = String(placeholder="Username", required=True)


class ExampleForm(QSForm):
    # BaseDataType / BaseInput behavior
    basic_string = String()
    default_string = String(default="Hello, world!")
    required_string = String(required=True)
    placeholder_string = String(placeholder="Enter text...")
    labeled_string = String(label="Custom label")
    constrained_string = String(
        default="abc",
        required=True,
        placeholder="3-10 characters",
        label="Constrained string",
        minlength=3,
        maxlength=10,
        pattern=r"[a-z]+",
    )

    # String combinations and boundary values
    empty_string = String(default="")
    zero_length_string = String(minlength=0, maxlength=0)
    long_string = String(default="x" * 100, maxlength=100)
    string_with_special_chars = String(default='<&>"\'')
    string_without_pattern = String(default="anything")

    # Checkbox
    checkbox_default_false = Checkbox()
    checkbox_default_true = Checkbox(default=True)
    checkbox_required = Checkbox(required=True)
    checkbox_labeled = Checkbox(label="Accept terms")
    checkbox_true_required = Checkbox(default=True, required=True)

    # Color
    color_default = Color()
    color_black = Color(default=(0, 0, 0))
    color_white = Color(default=(255, 255, 255))
    color_custom_rgb = Color(default=(100, 150, 200))
    color_hex = Color(default="#12abef")
    color_required = Color(required=True)
    color_labeled = Color(label="Accent color")

    # Email
    email_default = Email()
    email_populated = Email(default="user@example.com")
    email_required = Email(required=True)
    email_placeholder = Email(placeholder="name@example.com")
    email_multiple = Email(multiple=True)
    email_multiple_required = Email(multiple=True, required=True)
    email_labeled = Email(label="Contact email")

    # File
    file_default = File()
    file_required = File(required=True)
    file_image_accept = File(accept="image/*")
    file_specific_accept = File(accept=".png,.jpg,.webp")
    file_multiple = File(multiple=True)
    file_multiple_required = File(multiple=True, required=True)
    file_multiple_accept = File(accept=".pdf", multiple=True)
    file_labeled = File(label="Upload document")

    # Number
    number_default = Number()
    number_zero = Number(default=0)
    number_negative = Number(default=-10)
    number_decimal = Number(default=1.25)
    number_string_default = Number(default="42")
    number_min = Number(min=0)
    number_max = Number(max=100)
    number_bounds = Number(min=1, max=10)
    number_step = Number(step=0.5)
    number_all_constraints = Number(
        default=5,
        min=0,
        max=10,
        step=0.5,
        required=True,
        label="Constrained number",
        placeholder="0-10 in increments of 0.5",
    )

    # Password
    password_default = Password()
    password_required = Password(required=True)
    password_placeholder = Password(placeholder="Enter password")
    password_minlength = Password(minlength=8)
    password_maxlength = Password(maxlength=64)
    password_pattern = Password(pattern=r"[A-Za-z0-9]+")
    password_all_constraints = Password(
        required=True,
        placeholder="8-32 alphanumeric characters",
        minlength=8,
        maxlength=32,
        pattern=r"[A-Za-z0-9]+",
        label="Constrained password",
    )

    # Radio
    radio_default = Radio(value="option_a")
    radio_selected = Radio(value="option_b", selected=True)
    radio_required = Radio(value="option_c", required=True)
    radio_labeled = Radio(value="option_d", label="Option D")
    radio_selected_required = Radio(
        value="yes",
        selected=True,
        required=True,
        label="Yes",
    )

    # RadioSelector
    radio_selector_default = RadioSelector()
    radio_selector_no_options = RadioSelector(options=[])
    radio_selector_one_option = RadioSelector(options=["Only"])
    radio_selector_many_options = RadioSelector(
        options=["Small", "Medium", "Large"],
    )
    radio_selector_selected = RadioSelector(
        default="Medium",
        options=["Small", "Medium", "Large"],
    )
    radio_selector_required = RadioSelector(
        options=["Yes", "No"],
        required=True,
    )
    radio_selector_required_selected = RadioSelector(
        default="Yes",
        options=["Yes", "No"],
        required=True,
        label="Confirm",
    )
    radio_selector_custom_label = RadioSelector(
        default="Python",
        options=["Python", "Java", "Rust"],
        label="Favorite language",
    )

    # Range
    range_default = Range()
    range_zero = Range(default=0, min=0, max=100)
    range_minimum = Range(default=1, min=1, max=10)
    range_maximum = Range(default=10, min=1, max=10)
    range_decimal = Range(default=2.5, min=0, max=5, step=0.5)
    range_required = Range(required=True)
    range_labeled = Range(default=50, label="Volume")
    range_all_constraints = Range(
        default=5,
        min=0,
        max=10,
        step=1,
        required=True,
        label="Constrained range",
    )

    # URL
    url_default = URL()
    url_populated = URL(default="https://example.com")
    url_required = URL(required=True)
    url_placeholder = URL(placeholder="https://example.com")
    url_labeled = URL(label="Website URL")

    # Reset
    reset_default = Reset()
    reset_labeled = Reset(label="Clear all fields")

    # Date
    date_default = Date()
    date_string_default = Date(default="2026-01-15")
    date_object_default = Date(default=datetime.date(2026, 1, 15))
    date_min = Date(min="2020-01-01")
    date_max = Date(max="2030-12-31")
    date_bounds = Date(min="2020-01-01", max="2030-12-31")
    date_required = Date(required=True)
    date_labeled = Date(label="Start date")
    date_all_constraints = Date(
        default=datetime.date(2026, 6, 15),
        min=datetime.date(2026, 1, 1),
        max=datetime.date(2026, 12, 31),
        required=True,
        label="Constrained date",
    )

    # Time
    time_default = Time()
    time_string_default = Time(default="12:30")
    time_object_default = Time(default=datetime.time(12, 30))
    time_min = Time(min="09:00")
    time_max = Time(max="17:00")
    time_step = Time(step=900)
    time_required = Time(required=True)
    time_labeled = Time(label="Start time")
    time_all_constraints = Time(
        default=datetime.time(12, 30),
        min=datetime.time(9, 0),
        max=datetime.time(17, 0),
        step=900,
        required=True,
        label="Constrained time",
    )

    # DateTime
    datetime_default = DateTime()
    datetime_string_default = DateTime(default="2026-06-15T12:30")
    datetime_object_default = DateTime(
        default=datetime.datetime(2026, 6, 15, 12, 30)
    )
    datetime_min = DateTime(min="2026-01-01T00:00")
    datetime_max = DateTime(max="2026-12-31T23:59")
    datetime_step = DateTime(step=60)
    datetime_required = DateTime(required=True)
    datetime_labeled = DateTime(label="Scheduled at")
    datetime_all_constraints = DateTime(
        default=datetime.datetime(2026, 6, 15, 12, 30),
        min=datetime.datetime(2026, 1, 1),
        max=datetime.datetime(2026, 12, 31, 23, 59),
        step=60,
        required=True,
        label="Constrained date and time",
    )

    # Hidden
    hidden_empty = Hidden()
    hidden_value = Hidden(value="test-value")
    hidden_numeric_string = Hidden(value="123")

    # Button
    button_default = Button()
    button_value = Button(default="run")
    button_labeled = Button(label="Run operation")
    button_custom_attributes = Button(
        default="execute",
        label="Execute",
        inner_text="Run now",
        **{"data-action": "execute", "aria-label": "Execute action"},
    )

    # SubmitButton
    submit_default = SubmitButton()
    submit_custom_text = SubmitButton(inner_text="Save")
    submit_value = SubmitButton(default="save")
    submit_required = SubmitButton(required=True)
    submit_labeled = SubmitButton(label="Submit changes")
    submit_custom_attributes = SubmitButton(
        default="publish",
        label="Publish",
        inner_text="Publish now",
        **{"data-action": "publish"},
    )

    # Textarea
    textarea_default = Textarea()
    textarea_empty = Textarea(default="")
    textarea_populated = Textarea(default="Existing content")
    textarea_callable = Textarea(default=lambda: "Generated dynamically")
    textarea_placeholder = Textarea(placeholder="Write here...")
    textarea_required = Textarea(required=True)
    textarea_rows = Textarea(rows=5)
    textarea_cols = Textarea(cols=60)
    textarea_minlength = Textarea(minlength=10)
    textarea_maxlength = Textarea(maxlength=500)
    textarea_custom_label = Textarea(label="Description")
    textarea_all_constraints = Textarea(
        default="Example description",
        placeholder="Enter a description",
        required=True,
        label="Full description",
        rows=5,
        cols=60,
        minlength=10,
        maxlength=500,
        **{"data-test": "description"},
    )

    def __init__(self, action_name: str, instance_uuid: str):
        super().__init__(
            action_name=action_name,
            instance_uuid=instance_uuid,
        )