// Sidenotes fold on narrow screens. Where the margin is, a note floats
// beside its number and needs nothing. Where it is not, a marker takes the
// number's place, a square with a plus drawn as the copy button's icon is,
// and the note waits below its paragraph until the marker opens it. Without
// this script the notes stay inline, open, as before.
const plus =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8M8 12h8"/></svg>';
const minus =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 12h8"/></svg>';

// The breakpoint is the stylesheet's, under "Narrow screens".
const narrow = window.matchMedia("(max-width: 1000px)");

const notes = [...document.querySelectorAll(".sidenote")];

const markers = notes.map((note, index) => {
  note.id ||= `sidenote-${index + 1}`;
  note.classList.add("foldable", "folded");

  const marker = document.createElement("button");
  marker.className = "note-toggle";
  marker.type = "button";
  marker.setAttribute("aria-controls", note.id);
  marker.setAttribute("aria-expanded", "false");
  marker.setAttribute("aria-label", "Show sidenote");
  marker.innerHTML = plus;

  marker.addEventListener("click", () => {
    const open = note.classList.toggle("folded") === false;
    marker.setAttribute("aria-expanded", String(open));
    marker.setAttribute("aria-label", open ? "Hide sidenote" : "Show sidenote");
    marker.innerHTML = open ? minus : plus;
  });

  // A word joiner keeps the marker on the line of the word it follows.
  note.before("⁠", marker);
  return marker;
});

// Narrow, a note sits after the paragraph that holds its marker, or at the
// end of its list item, so it never splits a sentence, and a paragraph's
// notes keep their order; wide, it goes back beside its marker to float.
function place() {
  const last = new Map();
  notes.forEach((note, index) => {
    const marker = markers[index];
    const block = marker.closest("p, li");
    if (!narrow.matches || !block) marker.after(note);
    else if (block.matches("li")) block.append(note);
    else {
      (last.get(block) ?? block).after(note);
      last.set(block, note);
    }
  });
}

place();
narrow.addEventListener("change", place);
