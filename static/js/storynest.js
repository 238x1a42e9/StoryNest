/* StoryNest: small enhancements. Every feature also works without JavaScript,
   except the editor toolbar and live preview. */
(function () {
  "use strict";

  function csrfToken(form) {
    var input = form.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  // Ask before destructive actions that are plain POST forms.
  document.addEventListener("submit", function (event) {
    var message = event.target.getAttribute("data-confirm");
    if (message && !window.confirm(message)) event.preventDefault();
  });

  // Like button: update in place instead of reloading the page.
  document.querySelectorAll("[data-like-form]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var button = form.querySelector("button");
      button.disabled = true;
      fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken(form), "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      })
        .then(function (r) {
          if (!r.ok) throw new Error("Request failed");
          return r.json();
        })
        .then(function (data) {
          button.setAttribute("aria-pressed", data.liked ? "true" : "false");
          form.querySelector("[data-like-label]").textContent = data.liked ? "Liked" : "Like";
          form.querySelector("[data-like-count]").textContent = data.count;
        })
        .catch(function () {
          form.submit(); // fall back to a normal page load
        })
        .finally(function () {
          button.disabled = false;
        });
    });
  });

  // Markdown editor: toolbar buttons and live preview.
  document.querySelectorAll("[data-editor]").forEach(function (editor) {
    var textarea = editor.querySelector("textarea");
    var preview = editor.querySelector("[data-preview]");
    var toggle = editor.querySelector("[data-preview-toggle]");
    var form = editor.closest("form");

    function wrap(before, after, placeholder) {
      var start = textarea.selectionStart;
      var end = textarea.selectionEnd;
      var selected = textarea.value.slice(start, end) || placeholder;
      textarea.setRangeText(before + selected + after, start, end, "end");
      textarea.focus();
      textarea.setSelectionRange(start + before.length, start + before.length + selected.length);
    }

    function prefixLines(prefix, placeholder) {
      var start = textarea.selectionStart;
      var end = textarea.selectionEnd;
      var value = textarea.value;
      var lineStart = value.lastIndexOf("\n", start - 1) + 1;
      var chunk = value.slice(lineStart, end) || placeholder;
      var replaced = chunk.split("\n").map(function (line) { return prefix + line; }).join("\n");
      textarea.setRangeText(replaced, lineStart, end, "end");
      textarea.focus();
    }

    var actions = {
      bold: function () { wrap("**", "**", "bold text"); },
      italic: function () { wrap("*", "*", "italic text"); },
      heading: function () { prefixLines("## ", "Heading"); },
      quote: function () { prefixLines("> ", "Quote"); },
      list: function () { prefixLines("- ", "List item"); },
      code: function () { wrap("`", "`", "code"); },
      link: function () {
        var url = window.prompt("Link address (starting with https://)");
        if (url) wrap("[", "](" + url + ")", "link text");
      },
    };

    editor.querySelectorAll("[data-md]").forEach(function (button) {
      button.addEventListener("click", function () {
        if (!textarea.hidden) actions[button.getAttribute("data-md")]();
      });
    });

    toggle.addEventListener("click", function () {
      var showing = toggle.getAttribute("aria-pressed") === "true";
      if (showing) {
        toggle.setAttribute("aria-pressed", "false");
        toggle.textContent = "Preview";
        preview.hidden = true;
        textarea.hidden = false;
        textarea.focus();
        return;
      }
      var body = new URLSearchParams({ content: textarea.value });
      toggle.disabled = true;
      fetch(form.getAttribute("data-preview-url"), {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken(form), "Content-Type": "application/x-www-form-urlencoded" },
        credentials: "same-origin",
        body: body,
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          preview.innerHTML = data.html || "<p class='help'>Nothing to preview yet.</p>";
          toggle.setAttribute("aria-pressed", "true");
          toggle.textContent = "Edit";
          textarea.hidden = true;
          preview.hidden = false;
        })
        .catch(function () {
          preview.textContent = "Preview is not available right now.";
          preview.hidden = false;
        })
        .finally(function () { toggle.disabled = false; });
    });
  });
})();
