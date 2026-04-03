(function () {
  function reloadWithSelectedEvent(eventSelect) {
    var selectedEventId = eventSelect.value;
    var url = new URL(window.location.href);

    if (selectedEventId) {
      url.searchParams.set("event", selectedEventId);
    } else {
      url.searchParams.delete("event");
    }

    window.location.href = url.toString();
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Add form URL pattern in Django admin ends with '/add/'.
    if (!window.location.pathname.endsWith("/add/")) {
      return;
    }

    var eventSelect = document.getElementById("id_event");
    if (!eventSelect) {
      return;
    }

    eventSelect.addEventListener("change", function () {
      reloadWithSelectedEvent(eventSelect);
    });
  });
})();
