// A copy button in the corner of each code block, but not on a signature in
// the reference. It copies the code's text, not the button's, and shows a tick
// for two seconds once the clipboard has it.
const clipboard =
  '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="9" width="12" height="12" rx="2"/><path d="M5 15V5a2 2 0 0 1 2-2h10"/></svg>';
const tick =
  '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>';

for (const pre of document.querySelectorAll(".highlight:not(.doc-signature) > pre")) {
  const code = pre.querySelector("code");
  if (!code) continue;

  const button = document.createElement("button");
  button.className = "copy";
  button.type = "button";
  button.setAttribute("aria-label", "Copy code");
  button.innerHTML = clipboard;

  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(code.innerText);
    } catch {
      return;
    }
    button.innerHTML = tick;
    button.classList.add("copied");
    button.setAttribute("aria-label", "Copied");
    setTimeout(() => {
      button.innerHTML = clipboard;
      button.classList.remove("copied");
      button.setAttribute("aria-label", "Copy code");
    }, 2000);
  });

  pre.after(button);
}
