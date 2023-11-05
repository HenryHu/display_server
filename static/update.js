function cutTail(str) {
    return str.substring(0, str.length - 3);
}
function updateTime() {
    var now = new Date();
    var curDate = now.toLocaleString("en-US", {year: "numeric"}) + "/" +
        now.toLocaleString("en-US", {month: "2-digit"}) + "/" +
        now.toLocaleString("en-US", {day: "2-digit"}) + " " +
        now.toLocaleString("en-US", {weekday: "short"});
    var curTime = cutTail(now.toLocaleString("en-US", {
        hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true}));
    var pacificTime = cutTail(now.toLocaleString("en-US", {
        hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: true, timeZone: "PST8PDT"}));

    var dateDiv = document.getElementById('date');
    var timeDiv = document.getElementById('time');
    var pacificTimeDiv = document.getElementById('pactime');
    if (dateDiv != null) {
        dateDiv.textContent = curDate;
        timeDiv.textContent = curTime;
        pacificTimeDiv.textContent = pacificTime;
    }
}
setInterval(updateTime, 100);
updateTime();
