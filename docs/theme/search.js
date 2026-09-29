// Replaces the plugin's search/main.js: same worker and index, but
// groups section hits under their page instead of listing each as
// its own <article>, since the plugin indexes every heading as a
// separate entry.

function joinUrl(base, path) {
  if (path.substring(0, 1) === "/") return path;
  if (base.substring(base.length - 1) === "/") return base + path;
  return base + "/" + path;
}

function escapeHtml(value) {
  return value.replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

// Class names (AugmentedLocator) are single lunr tokens that stemming
// misses (a query for "Augmented" stems to "augment"), so every term
// is also sent as a wildcard: lunr ORs the two clauses, matching both
// stemmed prose and an exact, unstemmed class name.
function withPrefixes(query) {
  return query.split(/\s+/).map(asIndexed).filter(function (term) {
    return term.length > 0;
  }).map(function (term) {
    return term.charAt(term.length - 1) === '*' ? term : term + ' ' + term + '*';
  }).join(' ');
}

// A reader types text, not lunr query syntax: `tol:orange` would name a
// field, `~` and `^` demand a number, and a leading `+` or `-` makes a
// term required or excluded. Each term is trimmed of non-word ends as
// lunr's trimmer trimmed the indexed words, keeping a trailing `*`,
// and what syntax remains inside it is escaped. A hyphen inside a term
// stays bare, so the query splits there as the index did.
function asIndexed(term) {
  var wildcard = term.charAt(term.length - 1) === '*' ? '*' : '';
  var word = term.replace(/^\W+/, '').replace(/\W+$/, '');
  return word ? word.replace(/[:^~]/g, '\\$&') + wildcard : '';
}

var pageTitles = {};
fetch(joinUrl(base_url, "search/search_index.json"))
  .then(function (r) { return r.json(); })
  .then(function (data) {
    data.docs.forEach(function (doc) {
      if (doc.location.indexOf('#') === -1) pageTitles[doc.location] = doc.title;
    });
  });

function displayResults(results) {
  var search_results = document.getElementById("mkdocs-search-results");
  var order = [];
  var groups = {};
  results.forEach(function (result) {
    var pageLoc = result.location.split('#')[0];
    if (!groups[pageLoc]) {
      groups[pageLoc] = { title: pageTitles[pageLoc] || result.title, sections: [] };
      order.push(pageLoc);
    }
    if (result.location !== pageLoc) {
      groups[pageLoc].sections.push(result);
    } else {
      groups[pageLoc].title = result.title;
    }
  });
  search_results.innerHTML = order.map(function (pageLoc) {
    var group = groups[pageLoc];
    var html = '<article><h3><a href="' + joinUrl(base_url, pageLoc) + '">' +
      escapeHtml(group.title) + '</a></h3>';
    if (group.sections.length) {
      html += '<ul>' + group.sections.map(function (s) {
        return '<li><a href="' + joinUrl(base_url, s.location) + '">' +
          escapeHtml(s.title) + '</a></li>';
      }).join('') + '</ul>';
    }
    return html + '</article>';
  }).join('');
}

var searchInput = document.getElementById('mkdocs-search-query');
var ready = false;

var searchWorker = new Worker(joinUrl(base_url, "search/worker.js"));
searchWorker.postMessage({ init: true });
searchWorker.onmessage = function (e) {
  if (e.data.results) displayResults(e.data.results);
  if (e.data.allowSearch) {
    // The index just became searchable: run whatever was typed while
    // it was still loading, instead of leaving the panel empty.
    ready = true;
    var pending = withPrefixes(searchInput.value);
    if (pending.length > 0) searchWorker.postMessage({ query: pending });
  }
};

searchInput.addEventListener('input', function () {
  // A query of nothing but syntax trims to empty, and lunr would
  // return every page for it.
  var query = withPrefixes(this.value);
  if (query.length === 0) {
    document.getElementById("mkdocs-search-results").innerHTML = "";
  } else if (ready) {
    searchWorker.postMessage({ query: query });
  }
});
