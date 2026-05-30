(function () {
  var match = window.location.pathname.match(/^\/dashboard\/(articles|universities|institutes|majors)\/(\d+)\/edit\/$/);
  if (!match) return;

  var contentType = match[1];
  var objectId = match[2];
  var form = document.querySelector('form[method="post"], form');
  if (!form) return;

  function getCSRFToken() {
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  function createPanel() {
    var wrapper = document.createElement('section');
    wrapper.id = 'seo-analyzer-panel';
    wrapper.style.cssText = 'margin-top:16px;border:1px solid #d1d5db;border-radius:12px;padding:12px;background:#fff';

    var title = document.createElement('h3');
    title.textContent = 'SEO Analyzer (Phase 1)';
    title.style.cssText = 'margin:0 0 8px 0;font-size:16px;font-weight:700';

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Analyze SEO';
    btn.style.cssText = 'background:#0f766e;color:#fff;border:none;border-radius:8px;padding:8px 14px;cursor:pointer';

    var status = document.createElement('div');
    status.id = 'seo-analyzer-status';
    status.style.cssText = 'margin-top:10px;font-size:13px;color:#334155';

    var details = document.createElement('pre');
    details.id = 'seo-analyzer-details';
    details.style.cssText = 'margin-top:10px;white-space:pre-wrap;background:#f8fafc;border-radius:8px;padding:10px;font-size:12px;max-height:360px;overflow:auto';

    btn.addEventListener('click', function () {
      runAnalyze(btn, status, details);
    });

    wrapper.appendChild(title);
    wrapper.appendChild(btn);
    wrapper.appendChild(status);
    wrapper.appendChild(details);

    var target = form.querySelector('button[type="submit"]')?.closest('div') || form;
    target.parentNode.insertBefore(wrapper, target.nextSibling);
  }

  async function runAnalyze(btn, status, details) {
    try {
      btn.disabled = true;
      status.textContent = 'Saving draft...';

      var publishInput = document.getElementById('id_publish_status');
      if (publishInput) publishInput.value = 'unpublished';

      var fd = new FormData(form);
      var saveResp = await fetch(window.location.pathname, {
        method: 'POST',
        body: fd,
        headers: {
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
      });

      var saveJson = await saveResp.json().catch(function () { return {}; });
      if (!saveResp.ok || saveJson.status !== 'success') {
        status.textContent = 'Save draft failed';
        details.textContent = JSON.stringify(saveJson, null, 2);
        return;
      }

      status.textContent = 'Running SEO analysis...';
      var analyzeResp = await fetch('/dashboard/seo/analyze/' + contentType + '/' + objectId + '/', {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
      });
      var analyzeJson = await analyzeResp.json();
      if (!analyzeResp.ok || analyzeJson.status !== 'success') {
        status.textContent = 'Analyze failed';
        details.textContent = JSON.stringify(analyzeJson, null, 2);
        return;
      }

      status.textContent = 'Loading analysis details...';
      var detailResp = await fetch('/dashboard/seo/detail/' + contentType + '/' + objectId + '/', {
        method: 'GET',
        credentials: 'same-origin'
      });
      var detailJson = await detailResp.json();

      if (!detailResp.ok || detailJson.status !== 'success') {
        status.textContent = 'Could not load details';
        details.textContent = JSON.stringify(detailJson, null, 2);
        return;
      }

      status.textContent = 'Done: score ' + analyzeJson.seo_score + ' (' + analyzeJson.seo_grade + ')';
      details.textContent = JSON.stringify(detailJson, null, 2);
    } catch (err) {
      status.textContent = 'Unexpected error';
      details.textContent = String(err);
    } finally {
      btn.disabled = false;
    }
  }

  createPanel();
})();
