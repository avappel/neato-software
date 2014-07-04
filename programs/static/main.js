function main() {
  // Get initial data.
  update_battery();

  setInterval(update_battery, 10000);
}

function update_battery() {
  $.get("battery", function(data) {
    $("#voltage").text("Battery: " + data + "%");
  });
}

$(document).ready(main);
