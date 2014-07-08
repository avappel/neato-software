function main() {
  // Get initial data.
  updateBattery();

  logging = new Logging();

  setInterval(updateBattery, 10000);
  setInterval(function() {
    logging.update();
  }, 1000);
}

// A helper class for creating persistent log text.
function LogText(context, text, color, y) {
  this.context = context;
  this.text = text;
  this.size = 14;
  this.color = color;
  this.y = y;
  // Height of the canvas.
  this.height = this.context.canvas.height;
  // Keeps track of the current bounding box around text.
  var half_size = this.size / 2;
  this.bounding_box = [0, y + half_size, 500, y - half_size];

  this.__redraw = function() {
    this.clear();

    this.context.font = this.size + "px Arial";
    this.context.fillStyle = color;
    this.context.textAlign = "left";
    this.context.fillText(this.text, 0, this.y);
  };

  this.clear = function() {
    this.context.clearRect.apply(this.context, this.bounding_box);
  } 

  // Change the text.
  this.setText = function(text) {
    this.text = text;
    this.__redraw();
  };

  // Change the font.
  this.setFont = function(font) {
    this.context.font = font;
    this.__redraw();
  };

  // Change the color.
  this.setColor = function(color) {
    this.color = color;
    this.__redraw();
  }

  // Shifts the Y position of the text.
  this.move = function(y_ammount) {
    // Do this before we change the bounding box.
    this.clear();

    this.bounding_box[1] += y_ammount;
    this.bounding_box[3] += y_ammount;
    this.y += y_ammount;

    this.__redraw();
  };

  this.__redraw();
}

// Class for handling the log widget.
function LogDisplayer() {
  // An array of LogText objects currently being shown.
  this.showing = [];
  // Whether or not the displayer is clear.
  this.is_clear = false;
  
  // The canvas we are drawing on.
  this.context = document.getElementById("log_display").getContext("2d");
  // Set correct canvas size.
  this.height = $(window).height();
  this.context.canvas.height = this.height;

  this.clear = function() {
    this.context.clearRect(0, 0, 500, 500);

    this.context.font = "30px Arial";
    this.context.fillStyle = "#A3A375";
    this.context.textAlign = "center";
    this.context.fillText("No Messages.", 250, this.height / 2);

    this.is_clear = true;
  };

  this.addMessage = function(message) {
    if (this.is_clear) {
      // Remove "No Messages" text.
      this.context.clearRect(0, 0, 500, 500);
      this.is_clear = false;
    }

    // Format the message correctly.
    var date = new Date();
    var formatted = "[" + message[1] + "@" + date.toLocaleTimeString() + "] "
        + message[0] + ": " + message[2];

    // Move all the current messages up.
    var to_delete = 0;
    for (var i = 0; i < this.showing.length; ++i) {
      var value = this.showing[i];
      
      if (value.y <= 2) {
        value.erase();
        ++to_delete;
      } else {
        value.move(-18);
      }
    }
    // Remove old messages.
    for (var i = 0; i < to_delete; ++i) {
      this.showing.shift();
    }

    // Change the color if needed.
    if (message[0] == "WARNING") {
      var color = "#FF3300";
    } else if (message[0] == "ERROR") {
      var color = "#FF0000";
    } else if (message[0] == "FATAL") {
      var color = "#800000";
    } else {
      var color = "#000000";
    }

    // Add the new message.
    this.showing.push(new LogText(this.context, formatted,
        color, this.height - 9));
  };

  this.clear();
}

function updateBattery() {
  $.get("battery", function(data) {
    $("#voltage").text("Battery: " + data + "%");
  
    // Give it a nice color.
    if (Number(data) >= 95) {
      $("#voltage").css("color", "green");
    } else if (Number(data) <= 20) {
      $("#voltage").css("color", "red");
    }
  });
}

function Logging() {
  this.displayer = new LogDisplayer();

  this.update = function() {
    var displayer = this.displayer;

    $.get("logging", function(data) {
      var messages = JSON.parse(data);

      // Show the messages.
      for (var i = 0; i < messages.length; ++i) {
        displayer.addMessage(messages[i]);
      }
    });
  };
}

$(document).ready(main);
