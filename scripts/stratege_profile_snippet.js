// Run in the browser DevTools console on https://stratege.ru/playstation/users/dannymadcat
// (the game list there is loaded by JavaScript, so plain HTTP fetching does not see it).
// Result is copied to the clipboard: paste it into Claude Code; it replaces data/library_raw.txt.
// Line format: title|platform|got/total|diff|dur|last_trophy|plat_speed|stratege_path|hours_played
(async () => {
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const cells = tr => [...tr.querySelectorAll("td")].map(td => td.innerText.replace(/\s+/g, " ").trim());
  const findTable = re => [...$.fn.dataTable.tables()].find(t => re.test(t.querySelector("thead")?.innerText || ""));
  const norm = s => s.replace(/\s*\(.*?\)\s*$/, "").replace(/[’']/g, "'").toLowerCase().trim();

  // 1) collection tab
  pupf_type_cb("current"); await sleep(3500);
  let t = findTable(/Прогресс/); $(t).DataTable().page.len(-1).draw();
  const games = [...t.querySelectorAll("tbody tr")].map(tr => {
    const c = cells(tr); const a = tr.querySelector('a[href*="/games/"]');
    return { title: c[0].replace(/\((Европа|Весь мир|Оригинал|Трофеи)\)$/, "").trim(), last: c[1], pf: c[2], prog: c[3], diff: c[4], dur: c[5],
             speed: c[10] || "—", path: a ? a.getAttribute("href").split("/trophies")[0] : "" };
  });

  // 2) time-in-game tab
  pupf_type_cb("time"); await sleep(3500);
  t = findTable(/Время в игре/); $(t).DataTable().page.len(-1).draw();
  const toH = s => { const n = parseFloat(s.replace(/\s/g, "")); if (isNaN(n)) return "";
    if (/мин/.test(s)) return +(n / 60).toFixed(1); if (/сек/.test(s)) return 0; return n; };
  const hours = {};
  [...t.querySelectorAll("tbody tr")].forEach(tr => { const c = cells(tr); hours[norm(c[0]) + "|" + c[1]] = toH(c[4]); });

  const lines = games.map(g => [g.title, g.pf, g.prog, g.diff, g.dur, g.last, g.speed, g.path, hours[norm(g.title) + "|" + g.pf] ?? ""].join("|"));
  const head = document.body.innerText.match(/Всего игр\s*\d+|Пройдено на 100%\s*\d+|Общее завершение\s*\d+%|Время в играх\s*[\d\s]+час\w*/g) || [];
  const out = "# Stratege profile export " + new Date().toISOString().slice(0, 10) + "\n# " + head.join(" · ") +
    "\n# Format: title|platform|got/total|stratege_diff|stratege_dur|last_trophy|plat_speed|stratege_path|hours_played\n" + lines.join("\n") + "\n";
  copy(out);
  console.log(out);
  console.log("Скопировано в буфер: " + lines.length + " игр. Также посмотрите на шапку профиля: число платин/золота/серебра/бронзы.");
})();
