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

var searchWorker = new Worker(joinUrl(base_url, "search/worker.js"));
searchWorker.postMessage({ init: true });
searchWorker.onmessage = function (e) {
  if (e.data.results) displayResults(e.data.results);
};

document.getElementById('mkdocs-search-query').addEventListener('input', function () {
  var query = this.value;
  if (query.length === 0) {
    document.getElementById("mkdocs-search-results").innerHTML = "";
  } else {
    searchWorker.postMessage({ query: query });
  }
});
