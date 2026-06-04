// initialising socket connection
const socket = io({
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: Infinity,
  transports: ["websocket", "polling"]
});
var messagesLoaded;

// number of overall loaded messages on the page - works as counter
function initCounter(counter) {
  messagesLoaded = counter;
}

// converts timestamps to readable time format
document.addEventListener("DOMContentLoaded", function () {
  const timestamps = document.querySelectorAll(".timestamp");
  timestamps.forEach(function (timestampElement) {
    const rawTimestamp = timestampElement.getAttribute("data-timestamp");
    const formattedTimestamp = getTime(rawTimestamp);
    timestampElement.textContent = formattedTimestamp;
  });
});

// triggered when no more messages to load - then "load more" button disappears
socket.on("loading_finished", function () {
  const loadButton = document.getElementById("l");
  loadButton.style.display = "none";
});

function buildBubble(username, message, timestamp) {
  var isOwn = username === currentUser;
  var bubble = $("<div>").addClass("bubble").append(
    $("<div>").addClass("bubble-author").append(
      $(`<a href=/profile/${username}>`).text(username)
    ),
    $("<div>").text(message),
    $("<div>").addClass("bubble-time").text(getTime(timestamp))
  );
  return $("<div>").addClass("msg-row" + (isOwn ? " own" : "")).append(bubble);
}

// receives group of messages with "load more" button
socket.on("load", function (msg) {
  $("#messages").prepend(buildBubble(msg.username, msg.message, msg.timestamp));
  messagesLoaded = (parseInt(messagesLoaded, 10) + 1).toString();
});

// displays messages received from socket
socket.on("message", function (msg) {
  $("#messages").append(buildBubble(msg.username, msg.message, new Date().toISOString()));
  messagesLoaded = (parseInt(messagesLoaded, 10) + 1).toString();
});

// triggered when message length is more than expected
socket.on("message_too_long", function (msg_length) {
  const messageDisplay = document.getElementById("msg-panel");
  console.log(msg_length);
  messageDisplay.textContent = `The limit of message length (${msg_length} symbols) is exceeded`;
});

// formats posix timestamp to normal date
function getTime(time) {
  var dateObject = new Date(time);

  // formats the time components to ensure two digits
  hours = String(dateObject.getHours()).padStart(2, "0");
  minutes = String(dateObject.getMinutes()).padStart(2, "0");
  seconds = String(dateObject.getSeconds()).padStart(2, "0");

  // creates a string representing the time
  let formattedTime = `${hours}:${minutes}:${seconds}`;
  return formattedTime;
}

// send request to database to load messages with socket
function reqMessages() {
  socket.emit("request_message", messagesLoaded);
}

// sends messages to server with socket - the server log them into database
function sendMessage() {
  var message = $("#m").val();
  if (message.trim() !== "") {

    socket.emit("message", {
      message: message
    });
    $("#m").val("");
    $("#msg-panel").val("");
  }
}
