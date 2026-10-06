(function () {
  "use strict";

  var STRINGS = {
    en: {
      appTitle: "CRANIX QA Result Collector",
      planMeta: "{n} test cases loaded",
      import: "Import",
      exportMd: "Report (MD)",
      exportJson: "JSON",
      exportCsv: "CSV",
      runSection: "Test run",
      newRun: "New run",
      delete: "Delete",
      tester: "Tester",
      testerPlaceholder: "Your name",
      selectRun: "Run",
      noRuns: "No test runs yet.",
      createFirst: "Create the first test run to start collecting results.",
      namePrompt: "Tester name for the new run:",
      progress: "Progress",
      passed: "Passed",
      failed: "Failed",
      na: "N/A",
      notrun: "Not run",
      tier1: "Tier 1",
      total: "Total",
      filters: "Filters",
      tier: "Tier",
      allTiers: "All tiers",
      group: "Area",
      allGroups: "All areas",
      status: "Status",
      allStatuses: "All statuses",
      onlyFailed: "Only failed",
      search: "Search",
      searchPlaceholder: "Filter by id or title…",
      env: "Test environment (section 2.1)",
      preconditions: "Preconditions",
      steps: "Steps",
      expected: "Expected result",
      notes: "Notes",
      notesPlaceholder: "Notes (optional)",
      observed: "Observed result",
      observedPlaceholder: "What actually happened",
      log: "Log snippet",
      logPlaceholder: "Relevant log lines",
      blocksRelease: "Blocks release",
      updated: "Updated",
      saving: "Saving…",
      saved: "Saved",
      saveError: "Save failed",
      confirmDelete: "Delete this test run?",
      importError: "Could not import file",
      status_pass: "Pass",
      status_fail: "Fail",
      status_na: "N/A",
      status_notrun: "Not run"
    },
    de: {
      appTitle: "CRANIX QA Ergebnis-Erfassung",
      planMeta: "{n} Testfälle geladen",
      import: "Importieren",
      exportMd: "Bericht (MD)",
      exportJson: "JSON",
      exportCsv: "CSV",
      runSection: "Testlauf",
      newRun: "Neuer Lauf",
      delete: "Löschen",
      tester: "Tester",
      testerPlaceholder: "Ihr Name",
      selectRun: "Lauf",
      noRuns: "Noch keine Testläufe.",
      createFirst: "Ersten Testlauf anlegen, um Ergebnisse zu erfassen.",
      namePrompt: "Name des Testers für den neuen Lauf:",
      progress: "Fortschritt",
      passed: "Bestanden",
      failed: "Fehlgeschlagen",
      na: "N/A",
      notrun: "Nicht getestet",
      tier1: "Tier 1",
      total: "Gesamt",
      filters: "Filter",
      tier: "Tier",
      allTiers: "Alle Tiers",
      group: "Bereich",
      allGroups: "Alle Bereiche",
      status: "Status",
      allStatuses: "Alle Status",
      onlyFailed: "Nur fehlgeschlagene",
      search: "Suche",
      searchPlaceholder: "Nach ID oder Titel filtern…",
      env: "Testumgebung (Abschnitt 2.1)",
      preconditions: "Vorbedingungen",
      steps: "Schritte",
      expected: "Erwartetes Ergebnis",
      notes: "Notizen",
      notesPlaceholder: "Notizen (optional)",
      observed: "Beobachtetes Ergebnis",
      observedPlaceholder: "Was tatsächlich passiert ist",
      log: "Log-Auszug",
      logPlaceholder: "Relevante Log-Zeilen",
      blocksRelease: "Blockiert Release",
      updated: "Aktualisiert",
      saving: "Speichern…",
      saved: "Gespeichert",
      saveError: "Speichern fehlgeschlagen",
      confirmDelete: "Diesen Testlauf löschen?",
      importError: "Datei konnte nicht importiert werden",
      status_pass: "Bestanden",
      status_fail: "Fehlgeschlagen",
      status_na: "N/A",
      status_notrun: "Nicht getestet"
    }
  };

  var STATUSES = ["pass", "fail", "na", "notrun"];

  var lang = "en";
  var plan = null;
  var runs = [];
  var run = null;
  var saveTimer = null;

  var filters = { tier: "all", group: "all", status: "all", search: "" };

  var el = {
    planMeta: document.getElementById("planMeta"),
    langSelect: document.getElementById("langSelect"),
    importBtn: document.getElementById("importBtn"),
    importFile: document.getElementById("importFile"),
    runPanel: document.getElementById("runPanel"),
    progressPanel: document.getElementById("progressPanel"),
    filterPanel: document.getElementById("filterPanel"),
    envPanel: document.getElementById("envPanel"),
    casesPanel: document.getElementById("casesPanel"),
    content: document.getElementById("content"),
    toast: document.getElementById("toast")
  };

  function t(key) {
    return (STRINGS[lang] && STRINGS[lang][key]) || STRINGS.en[key] || key;
  }

  function esc(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function inlineMd(value) {
    var text = esc(value);
    text = text.replace(/`([^`]+)`/g, "<code>$1</code>");
    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    return text;
  }

  function L(field) {
    if (!field) return "";
    return field[lang] || field.en || "";
  }

  function resultFor(id) {
    if (!run) return {};
    return run.results[id] || {};
  }

  function statusOf(id) {
    var status = resultFor(id).status || "notrun";
    return STATUSES.indexOf(status) === -1 ? "notrun" : status;
  }

  function ensureResult(id) {
    if (!run.results[id]) {
      run.results[id] = {
        status: "notrun",
        notes: "",
        observed: "",
        log: "",
        blocksRelease: false
      };
    }
    return run.results[id];
  }

  function toast(message) {
    el.toast.textContent = message;
    el.toast.hidden = false;
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () {
      el.toast.hidden = true;
    }, 4000);
  }

  function api(path, options) {
    return fetch(path, options).then(function (response) {
      if (!response.ok) {
        return response
          .json()
          .catch(function () {
            return {};
          })
          .then(function (body) {
            throw new Error(body.error || "HTTP " + response.status);
          });
      }
      return response.json();
    });
  }

  function computeCounts() {
    var statuses = { pass: 0, fail: 0, na: 0, notrun: 0, total: plan.cases.length };
    var tier1 = { total: 0, pass: 0, fail: 0, na: 0, notrun: 0 };
    plan.cases.forEach(function (testCase) {
      var status = run ? statusOf(testCase.id) : "notrun";
      statuses[status] += 1;
      if (testCase.tier === 1) {
        tier1.total += 1;
        tier1[status] += 1;
      }
    });
    return { statuses: statuses, tier1: tier1 };
  }

  function render() {
    el.planMeta.textContent = t("planMeta").replace("{n}", plan ? plan.cases.length : 0);
    document.title = t("appTitle");
    document.documentElement.lang = lang;
    renderRunPanel();
    renderProgress();
    renderFilters();
    renderEnv();
    renderCases();
  }

  function renderRunPanel() {
    var options = runs
      .map(function (item) {
        var selected = run && item.id === run.id ? " selected" : "";
        var label = (item.tester || item.id) + " · " + (item.updated || "").slice(0, 16);
        return (
          '<option value="' + esc(item.id) + '"' + selected + ">" + esc(label) + "</option>"
        );
      })
      .join("");

    var html = "<h2>" + esc(t("runSection")) + "</h2>";
    if (runs.length) {
      html +=
        '<label class="field-label">' +
        esc(t("selectRun")) +
        '</label><select id="runSelect" class="select wide">' +
        options +
        "</select>";
    } else {
      html += '<p class="muted">' + esc(t("noRuns")) + "</p>";
    }
    if (run) {
      html +=
        '<label class="field-label">' +
        esc(t("tester")) +
        '</label><input id="testerInput" class="input" value="' +
        esc(run.tester || "") +
        '" placeholder="' +
        esc(t("testerPlaceholder")) +
        '">';
      html +=
        '<p class="muted small" id="saveState">' +
        esc(t("updated")) +
        ": " +
        esc((run.updated || "").slice(0, 19).replace("T", " ")) +
        "</p>";
    }
    html += '<div class="btn-row">';
    html += '<button id="newRunBtn" class="btn primary">' + esc(t("newRun")) + "</button>";
    if (run) {
      html += '<button id="deleteRunBtn" class="btn danger">' + esc(t("delete")) + "</button>";
    }
    html += "</div>";
    el.runPanel.innerHTML = html;
  }

  function renderProgress() {
    if (!run) {
      el.progressPanel.innerHTML = "";
      return;
    }
    var counts = computeCounts();
    var statuses = counts.statuses;
    var total = statuses.total || 1;
    var bar = STATUSES.map(function (status) {
      var width = (statuses[status] / total) * 100;
      return (
        '<span class="bar-seg seg-' +
        status +
        '" style="width:' +
        width.toFixed(2) +
        '%" title="' +
        esc(t("status_" + status)) +
        ": " +
        statuses[status] +
        '"></span>'
      );
    }).join("");

    var rows = STATUSES.map(function (status) {
      return (
        '<li><span class="dot seg-' +
        status +
        '"></span>' +
        esc(t("status_" + status)) +
        '<strong class="count">' +
        statuses[status] +
        "</strong></li>"
      );
    }).join("");

    var tier1 = counts.tier1;
    var tier1Percent = tier1.total ? Math.round((tier1.pass / tier1.total) * 100) : 0;

    el.progressPanel.innerHTML =
      "<h2>" +
      esc(t("progress")) +
      "</h2>" +
      '<div class="bar">' +
      bar +
      "</div>" +
      '<ul class="legend">' +
      rows +
      "</ul>" +
      '<div class="tier1-line"><span class="badge tier">T1</span>' +
      esc(t("tier1")) +
      '<strong class="count">' +
      tier1.pass +
      "/" +
      tier1.total +
      " (" +
      tier1Percent +
      '%)</strong></div>';
  }

  function renderFilters() {
    var tierOptions = [
      '<option value="all">' + esc(t("allTiers")) + "</option>",
      '<option value="0">Tier 0</option>',
      '<option value="1">Tier 1</option>',
      '<option value="2">Tier 2</option>'
    ].join("");

    var groupOptions =
      '<option value="all">' +
      esc(t("allGroups")) +
      "</option>" +
      plan.groups
        .map(function (group) {
          return (
            '<option value="' +
            esc(group.prefix) +
            '">' +
            esc(L(group.label)) +
            "</option>"
          );
        })
        .join("");

    var statusOptions =
      '<option value="all">' +
      esc(t("allStatuses")) +
      "</option>" +
      STATUSES.map(function (status) {
        return (
          '<option value="' + status + '">' + esc(t("status_" + status)) + "</option>"
        );
      }).join("") +
      '<option value="failed-only">' + esc(t("onlyFailed")) + "</option>";

    el.filterPanel.innerHTML =
      "<h2>" +
      esc(t("filters")) +
      "</h2>" +
      '<label class="field-label">' +
      esc(t("tier")) +
      '</label><select id="filterTier" class="select wide">' +
      tierOptions +
      "</select>" +
      '<label class="field-label">' +
      esc(t("group")) +
      '</label><select id="filterGroup" class="select wide">' +
      groupOptions +
      "</select>" +
      '<label class="field-label">' +
      esc(t("status")) +
      '</label><select id="filterStatus" class="select wide">' +
      statusOptions +
      "</select>" +
      '<label class="field-label">' +
      esc(t("search")) +
      '</label><input id="filterSearch" class="input wide" placeholder="' +
      esc(t("searchPlaceholder")) +
      '" value="' +
      esc(filters.search) +
      '">';

    document.getElementById("filterTier").value = filters.tier;
    document.getElementById("filterGroup").value = filters.group;
    document.getElementById("filterStatus").value = filters.status;
  }

  function renderEnv() {
    if (!run) {
      el.envPanel.innerHTML = "";
      return;
    }
    var rows = plan.envFields
      .map(function (field) {
        var value = (run.environment && run.environment[field.id]) || "";
        return (
          "<tr><th>" +
          esc(L(field.label)) +
          '</th><td><input class="input" data-env="' +
          esc(field.id) +
          '" value="' +
          esc(value) +
          '"></td></tr>'
        );
      })
      .join("");
    el.envPanel.innerHTML =
      "<details open><summary><h2>" +
      esc(t("env")) +
      "</h2></summary><table class=\"env-table\"><tbody>" +
      rows +
      "</tbody></table></details>";
  }

  function matchesFilters(testCase) {
    if (filters.tier !== "all" && String(testCase.tier) !== filters.tier) return false;
    if (filters.group !== "all" && testCase.group !== filters.group) return false;
    var status = run ? statusOf(testCase.id) : "notrun";
    if (filters.status === "failed-only" && status !== "fail") return false;
    if (filters.status !== "all" && filters.status !== "failed-only" && status !== filters.status) {
      return false;
    }
    if (filters.search) {
      var needle = filters.search.toLowerCase();
      var haystack = (testCase.id + " " + L(testCase.title)).toLowerCase();
      if (haystack.indexOf(needle) === -1) return false;
    }
    return true;
  }

  function caseCard(testCase) {
    var result = run ? resultFor(testCase.id) : {};
    var status = run ? statusOf(testCase.id) : "notrun";
    var steps = L(testCase.steps) || [];
    var stepsHtml = steps.length
      ? "<div class=\"field\"><span class=\"label\">" +
        esc(t("steps")) +
        "</span><ol>" +
        steps
          .map(function (step) {
            return "<li>" + inlineMd(step) + "</li>";
          })
          .join("") +
        "</ol></div>"
      : "";
    var preHtml = L(testCase.preconditions)
      ? "<p class=\"field\"><span class=\"label\">" +
        esc(t("preconditions")) +
        "</span> " +
        inlineMd(L(testCase.preconditions)) +
        "</p>"
      : "";
    var expHtml = L(testCase.expected)
      ? "<p class=\"field\"><span class=\"label\">" +
        esc(t("expected")) +
        "</span> " +
        inlineMd(L(testCase.expected)) +
        "</p>"
      : "";

    var statusOptions = STATUSES.map(function (option) {
      return (
        '<label class="opt opt-' +
        option +
        '"><input type="radio" name="status-' +
        esc(testCase.id) +
        '" data-case="' +
        esc(testCase.id) +
        '" data-status="' +
        option +
        '"' +
        (status === option ? " checked" : "") +
        "> " +
        esc(t("status_" + option)) +
        "</label>"
      );
    }).join("");

    return (
      '<article class="case tier-' +
      testCase.tier +
      (status === "fail" ? " is-fail" : "") +
      '" id="case-' +
      esc(testCase.id) +
      '" data-case="' +
      esc(testCase.id) +
      '">' +
      '<header class="case-head"><span class="case-id">' +
      esc(testCase.id) +
      '</span><h3>' +
      inlineMd(L(testCase.title)) +
      '</h3><span class="badges">' +
      '<span class="badge tier">T' +
      esc(testCase.tier) +
      '</span><span class="badge prio prio-' +
      esc(testCase.priority) +
      '">' +
      esc(testCase.priority) +
      '</span><span class="badge pkg">' +
      esc(testCase.package) +
      "</span></span></header>" +
      '<div class="case-body">' +
      preHtml +
      stepsHtml +
      expHtml +
      "</div>" +
      '<div class="case-status"><div class="status-options">' +
      statusOptions +
      "</div></div>" +
      '<div class="case-extra">' +
      '<textarea class="notes" data-notes="' +
      esc(testCase.id) +
      '" placeholder="' +
      esc(t("notesPlaceholder")) +
      '">' +
      esc(result.notes || "") +
      "</textarea>" +
      '<div class="fail-fields">' +
      '<label class="field-label">' +
      esc(t("observed")) +
      '</label><textarea data-observed="' +
      esc(testCase.id) +
      '" placeholder="' +
      esc(t("observedPlaceholder")) +
      '">' +
      esc(result.observed || "") +
      "</textarea>" +
      '<label class="field-label">' +
      esc(t("log")) +
      '</label><textarea data-log="' +
      esc(testCase.id) +
      '" placeholder="' +
      esc(t("logPlaceholder")) +
      '">' +
      esc(result.log || "") +
      "</textarea>" +
      '<label class="checkbox"><input type="checkbox" data-blocks="' +
      esc(testCase.id) +
      '"' +
      (result.blocksRelease ? " checked" : "") +
      "> " +
      esc(t("blocksRelease")) +
      "</label>" +
      "</div>" +
      "</div>" +
      "</article>"
    );
  }

  function renderCases() {
    if (!run) {
      el.casesPanel.innerHTML =
        '<div class="empty"><h2>' +
        esc(t("noRuns")) +
        "</h2><p>" +
        esc(t("createFirst")) +
        '</p><button id="emptyNewRun" class="btn primary">' +
        esc(t("newRun")) +
        "</button></div>";
      return;
    }
    var html = "";
    var currentGroup = null;
    var visible = 0;
    plan.cases.forEach(function (testCase) {
      if (!matchesFilters(testCase)) return;
      if (testCase.group !== currentGroup) {
        currentGroup = testCase.group;
        var group = plan.groups.filter(function (item) {
          return item.prefix === currentGroup;
        })[0];
        var label = (group || { label: { en: currentGroup } }).label;
        html += '<h2 class="group-title">' + esc(L(label)) + "</h2>";
      }
      html += caseCard(testCase);
      visible += 1;
    });
    if (!visible) {
      html = '<div class="empty"><p>' + esc(t("search")) + ": 0</p></div>";
    }
    el.casesPanel.innerHTML = html;
  }

  function updateSaveState(text) {
    var node = document.getElementById("saveState");
    if (node) node.textContent = text;
  }

  function scheduleSave() {
    if (!run) return;
    updateSaveState(t("saving"));
    clearTimeout(saveTimer);
    saveTimer = setTimeout(saveRun, 700);
  }

  function saveRun() {
    if (!run) return Promise.resolve();
    return api("/api/runs/" + encodeURIComponent(run.id), {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        tester: run.tester,
        language: run.language,
        environment: run.environment,
        results: run.results
      })
    })
      .then(function (updated) {
        run.updated = updated.updated;
        updateSaveState(t("saved") + " · " + (run.updated || "").slice(11, 19));
        refreshRuns();
      })
      .catch(function () {
        updateSaveState(t("saveError"));
        toast(t("saveError"));
      });
  }

  function refreshRuns() {
    return api("/api/runs").then(function (list) {
      runs = list || [];
      renderRunPanel();
    });
  }

  function openRun(id) {
    return api("/api/runs/" + encodeURIComponent(id)).then(function (data) {
      run = data;
      run.environment = run.environment || {};
      run.results = run.results || {};
      run.language = lang;
      render();
    });
  }

  function createRun() {
    var name = window.prompt(t("namePrompt"), "");
    if (name === null) return;
    api("/api/runs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tester: name.trim(), language: lang })
    }).then(function (created) {
      return refreshRuns().then(function () {
        return openRun(created.id);
      });
    });
  }

  function deleteRun() {
    if (!run) return;
    if (!window.confirm(t("confirmDelete"))) return;
    api("/api/runs/" + encodeURIComponent(run.id), { method: "DELETE" }).then(function () {
      run = null;
      return refreshRuns().then(function () {
        if (runs.length) return openRun(runs[0].id);
        render();
      });
    });
  }

  function exportRun(format) {
    if (!run) return;
    var link = document.createElement("a");
    link.href =
      "/api/runs/" +
      encodeURIComponent(run.id) +
      "/export?format=" +
      encodeURIComponent(format) +
      "&lang=" +
      encodeURIComponent(lang);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  function importRun(file) {
    var reader = new FileReader();
    reader.onload = function () {
      var data;
      try {
        data = JSON.parse(reader.result);
      } catch (error) {
        toast(t("importError"));
        return;
      }
      api("/api/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      })
        .then(function (created) {
          return refreshRuns().then(function () {
            return openRun(created.id);
          });
        })
        .catch(function () {
          toast(t("importError"));
        });
    };
    reader.readAsText(file);
  }

  el.langSelect.addEventListener("change", function () {
    lang = el.langSelect.value;
    localStorage.setItem("ck-lang", lang);
    if (run) run.language = lang;
    render();
    if (run) scheduleSave();
  });

  el.importBtn.addEventListener("click", function () {
    el.importFile.click();
  });

  el.importFile.addEventListener("change", function () {
    if (el.importFile.files.length) importRun(el.importFile.files[0]);
    el.importFile.value = "";
  });

  document.querySelectorAll("[data-export]").forEach(function (button) {
    button.addEventListener("click", function () {
      exportRun(button.getAttribute("data-export"));
    });
  });

  el.runPanel.addEventListener("click", function (event) {
    if (event.target.id === "newRunBtn") createRun();
    if (event.target.id === "deleteRunBtn") deleteRun();
  });

  el.runPanel.addEventListener("change", function (event) {
    if (event.target.id === "runSelect") openRun(event.target.value);
  });

  el.runPanel.addEventListener("input", function (event) {
    if (event.target.id === "testerInput" && run) {
      run.tester = event.target.value;
      scheduleSave();
    }
  });

  el.filterPanel.addEventListener("change", function (event) {
    if (event.target.id === "filterTier") filters.tier = event.target.value;
    if (event.target.id === "filterGroup") filters.group = event.target.value;
    if (event.target.id === "filterStatus") filters.status = event.target.value;
    renderCases();
  });

  el.filterPanel.addEventListener("input", function (event) {
    if (event.target.id === "filterSearch") {
      filters.search = event.target.value.trim();
      renderCases();
    }
  });

  el.envPanel.addEventListener("input", function (event) {
    var field = event.target.getAttribute("data-env");
    if (field && run) {
      run.environment[field] = event.target.value;
      scheduleSave();
    }
  });

  el.content.addEventListener("change", function (event) {
    var target = event.target;
    var caseId = target.getAttribute("data-case");
    if (caseId && target.getAttribute("data-status")) {
      var result = ensureResult(caseId);
      result.status = target.getAttribute("data-status");
      var card = document.getElementById("case-" + caseId);
      if (card) card.classList.toggle("is-fail", result.status === "fail");
      renderProgress();
      scheduleSave();
    }
    var blocksId = target.getAttribute("data-blocks");
    if (blocksId && run) {
      ensureResult(blocksId).blocksRelease = target.checked;
      scheduleSave();
    }
  });

  el.content.addEventListener("input", function (event) {
    var target = event.target;
    var caseId = target.getAttribute("data-notes");
    if (caseId) {
      ensureResult(caseId).notes = target.value;
      scheduleSave();
    }
    caseId = target.getAttribute("data-observed");
    if (caseId) {
      ensureResult(caseId).observed = target.value;
      scheduleSave();
    }
    caseId = target.getAttribute("data-log");
    if (caseId) {
      ensureResult(caseId).log = target.value;
      scheduleSave();
    }
  });

  el.casesPanel.addEventListener("click", function (event) {
    if (event.target.id === "emptyNewRun") createRun();
  });

  function init() {
    lang = localStorage.getItem("ck-lang") || "en";
    el.langSelect.value = lang;
    api("/api/plan")
      .then(function (data) {
        plan = data;
        return refreshRuns();
      })
      .then(function () {
        if (runs.length) {
          return openRun(runs[0].id);
        }
        render();
      })
      .catch(function (error) {
        el.planMeta.textContent = String(error);
      });
  }

  init();
})();
