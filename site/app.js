/* PricePulse BD — vanilla JS, no dependencies. Data: ./data/app.json + ./data/series/<id>.json */
(() => {
  'use strict';

  // ------------------------------------------------------------------ i18n
  const STR = {
    en: {
      skip: 'Skip to prices', headline: 'Dhaka bazaar prices, at a glance',
      hero_sub: 'Updated {date} · {n} essentials · Source: TCB daily market report',
      tile_basket: 'Core basket since 2020-21', tile_basket_sub: 'Index {v} (2020-21 = 100)',
      tile_month: 'Prices up in the past month', tile_month_sub: '{d} down · {f} unchanged',
      tile_alert: 'Sudden jumps right now', tile_alert_none: 'None in the last 2 weeks',
      tile_ramadan: 'Ramadan begins in', days: '{n} days', projected: 'projected',
      nav_prices: 'Prices', nav_alerts: 'Alerts', nav_trends: 'Trends', nav_festivals: 'Festivals',
      nav_forecast: 'Forecast',
      prices_title: "Today's prices", search: 'Search item', sort: 'Sort', sort_cat: 'Category',
      sort_rise: 'Biggest rise (1 month)', sort_fall: 'Biggest fall (1 month)', sort_name: 'Name',
      all: 'All', col_item: 'Item', col_price: 'Price (৳)', col_w1: '1 week', col_m1: '1 month',
      col_y1: '1 year', col_spark: '6 months', no_match: 'No item matches.',
      tap_hint: 'Tap an item for its history and 4-week range.', jump: 'Jump', per: 'per {u}',
      alerts_title: 'Sudden price jumps',
      alerts_sub: 'A jump means up 10% or more in two weeks and unusual for that item. In testing it caught {r} known supply shocks.',
      in2w: 'in 2 weeks', active: 'Active', show_all: 'Show all {n}', show_less: 'Show fewer',
      show_core: 'Show core basket only',
      trends_title: 'What got expensive',
      basket_title: 'Since 2020-21: import-dependent essentials {imp}, home-grown {dom}',
      basket_sub: 'Core basket price index, 2020-21 = 100', imp: 'Import-dependent',
      dom: 'Home-grown', other: 'Other', all_items: 'All items', month: 'Month',
      items_title: 'Change since 2020-21, by item', show_data: 'Show data',
      fest_title: 'Festival effect',
      fest_sub: 'Extra price change in the two weeks before, compared with normal times',
      fest_note: 'Onion, garlic and potato fall mainly because recent Ramadans coincided with harvest season.',
      ramadan_start: 'Ramadan', eid_ul_fitr: 'Eid-ul-Fitr', eid_ul_adha: 'Eid-ul-Adha',
      clear: 'Statistically clear', unclear: 'Uncertain', pricier: 'Pricier than usual',
      cheaper: 'Cheaper than usual', fest_tip: 'Above normal in {a} of {y} years',
      fc_title: 'How far can you trust a forecast?',
      fc_lead: "Best guess for next month's price: today's price.",
      fc_sub: 'We tested 6 forecasting models on {n} past forecasts. None beat it — so we show an honest range instead.',
      fc_models_title: 'Forecast error vs "no change", 4 weeks ahead',
      fc_range_title: 'How often the 80% range held',
      fc_typical: 'A typical price moves {p}% in four weeks.', wk: '{h} wk', worse: 'more error',
      m_ses: 'Exponential smoothing', m_gbm_median: 'Machine learning (median)',
      m_drift: 'Recent trend continues', m_gbm: 'Machine learning (average)',
      m_seasonal: 'Same as last year',
      foot_data: 'Data: Trading Corporation of Bangladesh (TCB) daily retail prices, Dhaka; World Food Programme.',
      foot_disc: 'Ranges are estimates, not guarantees.', foot_by: 'Built by',
      foot_updated: 'Data through {date}',
      now: 'Price now', r3m: '3 months', r1y: '1 year', rall: 'All',
      k_mid: 'Mid price', k_band: 'TCB lowest–highest', k_cone: '80% forecast range',
      k_today: "Today's price", next4: 'Next 4 weeks: likely range (80%)',
      fc_cov: "In testing, this item's range held {p}% of the time.",
      fc_none: 'Not enough history for a forecast yet.', date: 'Date', low: 'Lowest',
      high: 'Highest', load_fail: 'Could not load the data. Please refresh.',
      a_lang: 'Language', a_sections: 'Sections', a_category: 'Category', a_festival: 'Festival',
      a_close: 'Close', a_period: 'Period',
      nav_basket: 'My bazaar', basket_h: 'Your monthly bazaar',
      basket_lede: 'An example monthly basket for a family of four. Change the amounts to match your home — your list is saved only on this device.',
      b_item: 'Item', b_qty: 'Amount', b_cost: 'Cost', b_remove_col: 'Remove', b_add: '+ Add item',
      b_reset: 'Reset to example', b_total: 'This month', b_vs_m: 'vs 1 month ago', b_vs_y: 'vs 1 year ago',
      b_share: 'Where the money goes', b_drivers: 'What changed your bill since last year',
      b_excluded: '{n} item(s) have no price from a year ago and are left out of that comparison.',
      b_empty: 'Add items to see your bill.',
      b_src: 'Prices: midpoint of TCB Dhaka retail quotes. Your local market may differ.',
      remove: 'Remove {x}', less: 'Less {x}', more_of: 'More {x}', qty_of: 'Amount of {x}', year_ago: 'a year ago',
      cmp_title: 'Compare items', cmp_add: '+ Add item (up to 4)', cmp_none: 'Add at least one item to compare.',
      cmp_sub: 'Price index, start of period = 100. Lines above 100 got more expensive.',
      p_base: 'Since 2020-21', p_3y: '3 years', p_1y: '1 year',
      heat_title: 'When prices move', heat_cheaper: 'cheaper', heat_pricier: 'pricier', heat_tip: 'vs previous month',
      heat_sub: 'Month-on-month price change, core items. Tap a cell to open the item.',
      season_title: 'A typical year',
      season_txt: 'Usually cheapest in {lo} and priciest in {hi} — about {amp}% apart ({n} years of data).',
      season_flat: 'No clear seasonal pattern — prices swing only about {amp}% across the year.',
      season_none: 'Not enough years of data yet to show a seasonal pattern.', vs_avg: 'vs yearly average',
      share: 'Share', copied: 'Link copied',
      path_title: 'Average price around {f}: {item}',
      path_sub: 'Line = average of {n} years; shaded = lowest to highest year. Tap an item in the list above to switch.',
      avg: 'Average', range_years: 'Range across years', day0: '{f} day', days_before: '{n} days before',
      days_after: '{n} days after', d_short: 'd',
    },
    bn: {
      skip: 'দামের তালিকায় যান', headline: 'ঢাকার বাজারদর, এক নজরে',
      hero_sub: 'হালনাগাদ {date} · {n}টি নিত্যপণ্য · সূত্র: টিসিবির দৈনিক বাজারদর',
      tile_basket: '২০২০-২১ থেকে মূল ঝুড়ির দাম', tile_basket_sub: 'সূচক {v} (২০২০-২১ = ১০০)',
      tile_month: 'গত এক মাসে দাম বেড়েছে', tile_month_sub: '{d}টির কমেছে · {f}টি অপরিবর্তিত',
      tile_alert: 'এই মুহূর্তে হঠাৎ বৃদ্ধি', tile_alert_none: 'গত ২ সপ্তাহে নেই',
      tile_ramadan: 'রমজান শুরু হতে বাকি', days: '{n} দিন', projected: 'সম্ভাব্য',
      nav_prices: 'দাম', nav_alerts: 'সতর্কতা', nav_trends: 'প্রবণতা', nav_festivals: 'উৎসব',
      nav_forecast: 'পূর্বাভাস',
      prices_title: 'আজকের দাম', search: 'পণ্য খুঁজুন', sort: 'সাজান', sort_cat: 'শ্রেণি',
      sort_rise: 'সবচেয়ে বেড়েছে (১ মাস)', sort_fall: 'সবচেয়ে কমেছে (১ মাস)', sort_name: 'নাম',
      all: 'সব', col_item: 'পণ্য', col_price: 'দাম (৳)', col_w1: '১ সপ্তাহ', col_m1: '১ মাস',
      col_y1: '১ বছর', col_spark: '৬ মাস', no_match: 'কোনো পণ্য মেলেনি।',
      tap_hint: 'ইতিহাস ও ৪ সপ্তাহের সম্ভাব্য দাম দেখতে পণ্যে চাপুন।', jump: 'হঠাৎ বৃদ্ধি',
      per: 'প্রতি {u}',
      alerts_title: 'হঠাৎ দাম বৃদ্ধি',
      alerts_sub: 'দুই সপ্তাহে ১০% বা তার বেশি বৃদ্ধি, যা ওই পণ্যের জন্য অস্বাভাবিক। পরীক্ষায় জানা সরবরাহ-সংকটের {r}টি ধরা পড়েছে।',
      in2w: '২ সপ্তাহে', active: 'চলমান', show_all: 'সব {n}টি দেখুন', show_less: 'কম দেখুন',
      show_core: 'শুধু মূল ঝুড়ি দেখুন',
      trends_title: 'কোন পণ্যের দাম বেশি বেড়েছে',
      basket_title: '২০২০-২১ থেকে: আমদানিনির্ভর নিত্যপণ্য {imp}, দেশি পণ্য {dom}',
      basket_sub: 'মূল ঝুড়ির মূল্যসূচক, ২০২০-২১ = ১০০', imp: 'আমদানিনির্ভর', dom: 'দেশি',
      other: 'অন্যান্য', all_items: 'সব পণ্য', month: 'মাস',
      items_title: '২০২০-২১ থেকে পরিবর্তন, পণ্যভিত্তিক', show_data: 'ডেটা দেখুন',
      fest_title: 'উৎসবের প্রভাব',
      fest_sub: 'উৎসবের আগের দুই সপ্তাহে স্বাভাবিক সময়ের তুলনায় দামের বাড়তি পরিবর্তন',
      fest_note: 'পেঁয়াজ, রসুন ও আলুর দাম কমার মূল কারণ—সাম্প্রতিক রমজানগুলো ফসল তোলার মৌসুমে পড়েছে।',
      ramadan_start: 'রমজান', eid_ul_fitr: 'ঈদুল ফিতর', eid_ul_adha: 'ঈদুল আজহা',
      clear: 'পরিসংখ্যানে স্পষ্ট', unclear: 'অনিশ্চিত', pricier: 'স্বাভাবিকের চেয়ে বেশি দাম',
      cheaper: 'স্বাভাবিকের চেয়ে কম দাম', fest_tip: '{y} বছরের মধ্যে {a} বছর স্বাভাবিকের বেশি',
      fc_title: 'পূর্বাভাস কতটা নির্ভরযোগ্য?',
      fc_lead: 'আগামী মাসের দামের সেরা অনুমান: আজকের দামই।',
      fc_sub: '{n}টি অতীত পূর্বাভাসে ৬টি মডেল পরীক্ষা করা হয়েছে। কোনোটিই এর চেয়ে ভালো করেনি—তাই আমরা দামের একটি বাস্তবসম্মত সম্ভাব্য সীমা দেখাই।',
      fc_models_title: '“দাম অপরিবর্তিত” ধরার তুলনায় পূর্বাভাসের ভুল, ৪ সপ্তাহ পরে',
      fc_range_title: '৮০% সীমা কতবার ঠিক ছিল',
      fc_typical: 'চার সপ্তাহে একটি পণ্যের দাম সাধারণত {p}% বদলায়।', wk: '{h} সপ্তাহ',
      worse: 'বেশি ভুল',
      m_ses: 'এক্সপোনেনশিয়াল স্মুদিং', m_gbm_median: 'মেশিন লার্নিং (মধ্যমা)',
      m_drift: 'সাম্প্রতিক ধারা চলবে', m_gbm: 'মেশিন লার্নিং (গড়)', m_seasonal: 'গত বছরের মতো',
      foot_data: 'তথ্য: ট্রেডিং কর্পোরেশন অব বাংলাদেশ (টিসিবি)-র দৈনিক খুচরা বাজারদর, ঢাকা; বিশ্ব খাদ্য কর্মসূচি।',
      foot_disc: 'সীমাগুলো অনুমান, নিশ্চয়তা নয়।', foot_by: 'নির্মাতা:',
      foot_updated: '{date} পর্যন্ত তথ্য',
      now: 'এখনকার দাম', r3m: '৩ মাস', r1y: '১ বছর', rall: 'সব',
      k_mid: 'মধ্যম দাম', k_band: 'টিসিবির সর্বনিম্ন–সর্বোচ্চ', k_cone: '৮০% পূর্বাভাস সীমা',
      k_today: 'আজকের দাম', next4: 'আগামী ৪ সপ্তাহ: সম্ভাব্য সীমা (৮০%)',
      fc_cov: 'পরীক্ষায় এই পণ্যের সীমা {p}% ক্ষেত্রে ঠিক ছিল।',
      fc_none: 'পূর্বাভাসের জন্য এখনো যথেষ্ট তথ্য নেই।', date: 'তারিখ', low: 'সর্বনিম্ন',
      high: 'সর্বোচ্চ', load_fail: 'তথ্য লোড করা যায়নি। পাতাটি আবার খুলুন।',
      a_lang: 'ভাষা', a_sections: 'অংশসমূহ', a_category: 'শ্রেণি', a_festival: 'উৎসব',
      a_close: 'বন্ধ করুন', a_period: 'সময়কাল',
      nav_basket: 'আমার বাজার', basket_h: 'আপনার মাসিক বাজার',
      basket_lede: 'চার সদস্যের একটি পরিবারের উদাহরণ মাসিক বাজার। আপনার বাসার সঙ্গে মিলিয়ে পরিমাণ বদলান—তালিকাটি শুধু এই ডিভাইসে সংরক্ষিত থাকে।',
      b_item: 'পণ্য', b_qty: 'পরিমাণ', b_cost: 'খরচ', b_remove_col: 'বাদ দিন', b_add: '+ পণ্য যোগ করুন',
      b_reset: 'উদাহরণে ফিরে যান', b_total: 'এই মাসের খরচ', b_vs_m: '১ মাস আগের তুলনায়', b_vs_y: '১ বছর আগের তুলনায়',
      b_share: 'টাকা কোথায় খরচ হয়', b_drivers: 'গত বছরের তুলনায় কোন পণ্যে খরচ বদলেছে',
      b_excluded: '{n}টি পণ্যের এক বছর আগের দাম নেই, তাই ওই তুলনা থেকে বাদ রাখা হয়েছে।',
      b_empty: 'খরচ দেখতে পণ্য যোগ করুন।',
      b_src: 'দাম: টিসিবির ঢাকা খুচরা বাজারদরের মধ্যম মান। আপনার এলাকার বাজারে দাম ভিন্ন হতে পারে।',
      remove: '{x} বাদ দিন', less: '{x} কমান', more_of: '{x} বাড়ান', qty_of: '{x}-এর পরিমাণ', year_ago: '১ বছর আগে',
      cmp_title: 'পণ্যের তুলনা', cmp_add: '+ পণ্য যোগ করুন (সর্বোচ্চ ৪টি)', cmp_none: 'তুলনার জন্য অন্তত একটি পণ্য যোগ করুন।',
      cmp_sub: 'মূল্যসূচক, সময়ের শুরু = ১০০। ১০০-র ওপরে থাকা রেখা মানে দাম বেড়েছে।',
      p_base: '২০২০-২১ থেকে', p_3y: '৩ বছর', p_1y: '১ বছর',
      heat_title: 'কখন দাম বদলায়', heat_cheaper: 'কমেছে', heat_pricier: 'বেড়েছে', heat_tip: 'আগের মাসের তুলনায়',
      heat_sub: 'আগের মাসের তুলনায় দামের পরিবর্তন, মূল পণ্য। পণ্যটি খুলতে ঘরে চাপুন।',
      season_title: 'সাধারণ একটি বছর',
      season_txt: 'সাধারণত {lo} মাসে সবচেয়ে সস্তা আর {hi} মাসে সবচেয়ে দামি—পার্থক্য প্রায় {amp}% ({n} বছরের তথ্য)।',
      season_flat: 'স্পষ্ট মৌসুমি ধারা নেই—বছরজুড়ে দাম ওঠানামা করে মাত্র প্রায় {amp}%।',
      season_none: 'মৌসুমি ধারা দেখানোর মতো যথেষ্ট বছরের তথ্য এখনো নেই।', vs_avg: 'বার্ষিক গড়ের তুলনায়',
      share: 'শেয়ার', copied: 'লিংক কপি হয়েছে',
      path_title: '{f}-এর আগে-পরে গড় দাম: {item}',
      path_sub: 'রেখা = {n} বছরের গড়; ছায়া = বছরভেদে সর্বনিম্ন থেকে সর্বোচ্চ। বদলাতে ওপরের তালিকার কোনো পণ্যে চাপুন।',
      avg: 'গড়', range_years: 'বছরভেদে সীমা', day0: '{f}-এর দিন', days_before: '{n} দিন আগে',
      days_after: '{n} দিন পরে', d_short: ' দিন',
    },
  };

  const state = {
    lang: 'en', app: null, cat: 'all', q: '', sort: 'cat', fest: 'ramadan_start', range: 'r1y',
    item: null, showAllItems: false, showAllAlerts: false, showAllPrices: false, series: new Map(),
    basket: null, compare: ['rice_coarse', 'atta_loose', 'soybean_loose', 'onion_local'], cmpSlot: {},
    cmpPeriod: 'base', festItem: null,
  };
  try {
    const saved = localStorage.getItem('pp-lang');
    state.lang = saved || ((navigator.language || '').toLowerCase().startsWith('bn') ? 'bn' : 'en');
  } catch { /* storage unavailable: keep default */ }
  const params = new URLSearchParams(location.search);   // shareable: ?lang=bn&item=onion_local
  if (['en', 'bn'].includes(params.get('lang'))) state.lang = params.get('lang');

  const $ = (sel, root = document) => root.querySelector(sel);
  const t = (key, vars) => {
    let s = STR[state.lang][key] ?? STR.en[key] ?? key;
    if (vars) for (const k in vars) s = s.replaceAll(`{${k}}`, vars[k]);
    return s;
  };
  const el = (tag, cls, text) => {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  };
  const NS = 'http://www.w3.org/2000/svg';
  const svg = (tag, attrs) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  };
  const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

  // ------------------------------------------------------------------ formatting
  const loc = () => (state.lang === 'bn' ? 'bn-BD' : 'en-GB');
  const num = (v, d = 0) => new Intl.NumberFormat(loc(), { maximumFractionDigits: d }).format(v);
  const price = (v) => (v == null ? '–' : num(v, v < 100 && v % 1 ? 1 : 0));
  const taka = (v) => '৳' + price(v);
  const span = (lo, hi) => (lo === hi ? taka(lo) : `${taka(lo)}–${price(hi)}`);
  const pct = (v, d) => {
    if (v == null) return '–';
    const digits = d ?? (Math.abs(v) < 10 ? 1 : 0);
    return (v > 0 ? '+' : v < 0 ? '−' : '') + num(Math.abs(v), digits) + '%';
  };
  const utc = (iso) => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +(iso.slice(8, 10) || 1));
  const fmtDate = (ms, opts = { day: 'numeric', month: 'short', year: 'numeric' }) =>
    new Intl.DateTimeFormat(loc(), { ...opts, timeZone: 'UTC' }).format(new Date(ms));
  const name = (it) => (state.lang === 'bn' ? it.bn : it.en);
  const unit = (it) => (state.lang === 'bn' ? it.unit_bn : it.unit);
  const catName = (id) => (state.lang === 'bn'
    ? state.app.categories.find((c) => c.id === id)?.bn ?? id : id);
  const itemById = (id) => state.app.items.find((i) => i.id === id);

  // ------------------------------------------------------------------ tooltip
  const tip = $('#tip');
  function showTip(x, y, header, rows) {
    tip.replaceChildren();
    if (header) tip.append(el('div', 'tip-h', header));
    for (const r of rows) {
      const row = el('div', 'tip-r');
      if (r.color) { const k = el('i'); k.style.borderColor = r.color; row.append(k); }
      row.append(el('b', null, r.value));
      if (r.label) row.append(el('span', null, r.label));
      tip.append(row);
    }
    tip.hidden = false;
    const w = tip.offsetWidth, h = tip.offsetHeight;
    let left = x + 14, top = y - h - 12;
    if (left + w > innerWidth - 8) left = x - w - 14;
    if (left < 8) left = 8;
    if (top < 8) top = y + 16;
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  }
  const hideTip = () => { tip.hidden = true; };

  // ------------------------------------------------------------------ charts
  function niceTicks(min, max, count = 5) {
    const step0 = (max - min) / Math.max(1, count);
    const mag = 10 ** Math.floor(Math.log10(step0));
    const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => s >= step0) || step0;
    const out = [];
    for (let v = Math.ceil(min / step) * step; v <= max + 1e-9; v += step) out.push(+v.toFixed(6));
    return out;
  }

  function timeTicks(t0, t1, maxTicks) {
    const years = (t1 - t0) / (365.25 * 864e5);
    const ticks = [];
    const d = new Date(t0);
    if (years > 2.5) {
      const step = Math.max(1, Math.ceil(years / maxTicks));
      for (let y = d.getUTCFullYear() + 1; Date.UTC(y, 0, 1) <= t1; y += step) {
        ticks.push({ t: Date.UTC(y, 0, 1), label: fmtDate(Date.UTC(y, 0, 1), { year: 'numeric' }) });
      }
      return ticks;
    }
    const months = Math.max(1, Math.round(years * 12));
    const step = Math.max(1, Math.ceil(months / maxTicks));
    let y = d.getUTCFullYear(), m = d.getUTCMonth() + 1;
    for (let i = 0; Date.UTC(y, m, 1) <= t1; i++, m++) {
      if (m > 11) { m = 0; y++; }
      if (i % step) continue;
      const ms = Date.UTC(y, m, 1);
      ticks.push({ t: ms, label: fmtDate(ms, m === 0 ? { month: 'short', year: '2-digit' } : { month: 'short' }) });
    }
    return ticks;
  }

  /* cfg: { lines:[{label,color,pts:[[t,y]],dotted}], band:{color,pts:[[t,lo,hi]]},
            cone:{color,pts:[[t,lo,hi]]}, endLabels, yFmt, tip(t)->{header,rows}, label } */
  function lineChart(host, cfg) {
    host._ro?.disconnect();
    const draw = () => {
      const W = host.clientWidth, H = host.clientHeight;
      if (!W || !H) return;
      const m = { l: 46, r: cfg.endLabels ? 46 : 12, t: 10, b: 26 };
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const ts = [], ys = [];
      for (const ln of cfg.lines) for (const p of ln.pts) { ts.push(p[0]); ys.push(p[1]); }
      for (const a of [cfg.band, cfg.cone]) if (a) for (const p of a.pts) { ts.push(p[0]); ys.push(p[1], p[2]); }
      if (!ts.length) return;
      const t0 = Math.min(...ts), t1 = Math.max(...ts);
      let y0 = Math.min(...ys), y1 = Math.max(...ys);
      const pad = (y1 - y0 || y1 * 0.1 || 1) * 0.08;
      y0 -= pad; y1 += pad;
      const X = (v) => m.l + ((v - t0) / (t1 - t0 || 1)) * pw;
      const Y = (v) => m.t + (1 - (v - y0) / (y1 - y0)) * ph;
      const yFmt = cfg.yFmt || ((v) => num(v, 1));

      const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', tabindex: 0, 'aria-label': cfg.label || '' });
      for (const v of niceTicks(y0, y1, 4)) {
        root.append(svg('line', { class: 'grid', x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v) }));
        const tx = svg('text', { x: m.l - 8, y: Y(v) + 4, 'text-anchor': 'end' });
        tx.textContent = yFmt(v);
        root.append(tx);
      }
      root.append(svg('line', { class: 'axis', x1: m.l, x2: W - m.r, y1: m.t + ph, y2: m.t + ph }));
      for (const k of (cfg.xTicks ? cfg.xTicks(t0, t1) : timeTicks(t0, t1, Math.max(2, Math.floor(pw / 72))))) {
        const tx = svg('text', { x: X(k.t), y: H - 7, 'text-anchor': 'middle' });
        tx.textContent = k.label;
        root.append(tx);
      }
      const area = (a, opacity) => {
        const up = a.pts.map((p) => `${X(p[0]).toFixed(1)},${Y(p[2]).toFixed(1)}`);
        const dn = a.pts.map((p) => `${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).reverse();
        root.append(svg('polygon', { points: up.concat(dn).join(' '), fill: a.color, 'fill-opacity': opacity }));
      };
      for (const mk of cfg.markers || []) {
        root.append(svg('line', { class: 'cross', x1: X(mk.x), x2: X(mk.x), y1: m.t, y2: m.t + ph }));
        const tx = svg('text', { x: X(mk.x) + 5, y: m.t + 11 });
        tx.textContent = mk.label;
        root.append(tx);
      }
      if (cfg.band) area(cfg.band, 0.14);
      if (cfg.cone) area(cfg.cone, 0.26);
      const ends = [];
      for (const ln of cfg.lines) {
        const dAttr = ln.pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)} ${Y(p[1]).toFixed(1)}`).join('');
        const path = svg('path', { d: dAttr, fill: 'none', stroke: ln.color, 'stroke-width': 2,
          'stroke-linejoin': 'round', 'stroke-linecap': 'round' });
        if (ln.dotted) path.setAttribute('stroke-dasharray', '1 5');
        root.append(path);
        if (cfg.endLabels) {
          const p = ln.pts[ln.pts.length - 1];
          ends.push({ x: X(p[0]), y: Y(p[1]), color: ln.color, text: yFmt(p[1]) });
        }
      }
      ends.sort((a, b) => a.y - b.y);
      for (let i = 1; i < ends.length; i++) {
        if (ends[i].y - ends[i - 1].y < 15) { ends[i - 1].ly = ends[i - 1].y - 7; ends[i].ly = ends[i].y + 7; }
      }
      for (const e of ends) {
        root.append(svg('circle', { cx: e.x, cy: e.y, r: 4, fill: e.color, stroke: css('--surface'), 'stroke-width': 2 }));
        const tx = svg('text', { class: 'end', x: e.x + 8, y: (e.ly ?? e.y) + 4 });
        tx.textContent = e.text;
        root.append(tx);
      }

      // hover layer: the crosshair finds the X, one tooltip lists every series
      const xs = [...new Set(ts)].sort((a, b) => a - b);
      const cross = svg('line', { class: 'cross', y1: m.t, y2: m.t + ph, visibility: 'hidden' });
      const dots = cfg.lines.filter((l) => !l.dotted).map((ln) => {
        const c = svg('circle', { r: 4, fill: ln.color, stroke: css('--surface'), 'stroke-width': 2, visibility: 'hidden' });
        root.append(c);
        return { c, ln };
      });
      root.append(cross);
      let idx = xs.length - 1;
      const nearest = (arr, v) => {
        let lo = 0, hi = arr.length - 1;
        while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (arr[mid] < v) lo = mid; else hi = mid; }
        return Math.abs(arr[lo] - v) <= Math.abs(arr[hi] - v) ? lo : hi;
      };
      const show = (i) => {
        idx = Math.max(0, Math.min(xs.length - 1, i));
        const tv = xs[idx], px = X(tv);
        cross.setAttribute('x1', px); cross.setAttribute('x2', px);
        cross.setAttribute('visibility', 'visible');
        for (const { c, ln } of dots) {
          const p = ln.pts.find((q) => q[0] === tv);
          if (p) { c.setAttribute('cx', px); c.setAttribute('cy', Y(p[1])); c.setAttribute('visibility', 'visible'); }
          else c.setAttribute('visibility', 'hidden');
        }
        const box = root.getBoundingClientRect();
        const info = cfg.tip ? cfg.tip(tv) : {
          header: cfg.xFmt ? cfg.xFmt(tv) : fmtDate(tv),
          rows: cfg.lines.map((ln) => { const p = ln.pts.find((q) => q[0] === tv); return p && { color: ln.color, value: yFmt(p[1]), label: ln.label }; }).filter(Boolean),
        };
        showTip(box.left + (px / W) * box.width, box.top + m.t + 10, info.header, info.rows);
      };
      const hide = () => {
        cross.setAttribute('visibility', 'hidden');
        for (const { c } of dots) c.setAttribute('visibility', 'hidden');
        hideTip();
      };
      const hit = svg('rect', { x: m.l, y: m.t, width: pw, height: ph, fill: 'transparent' });
      hit.addEventListener('pointermove', (ev) => {
        const box = root.getBoundingClientRect();
        const vx = ((ev.clientX - box.left) / box.width) * W;
        show(nearest(xs, t0 + ((vx - m.l) / pw) * (t1 - t0)));
      });
      hit.addEventListener('pointerleave', hide);
      root.append(hit);
      root.addEventListener('focus', () => show(idx));
      root.addEventListener('blur', hide);
      root.addEventListener('keydown', (ev) => {
        if (ev.key === 'ArrowLeft') { show(idx - 1); ev.preventDefault(); }
        if (ev.key === 'ArrowRight') { show(idx + 1); ev.preventDefault(); }
      });
      host.replaceChildren(root);
    };
    host._ro = new ResizeObserver(draw);
    host._ro.observe(host);
    draw();
  }

  /* rows: [{label, value, text, color, hollow, tip:{header, rows}}] ; zero-based or diverging */
  function lollipop(host, rows, { min, max }) {
    host.replaceChildren();
    const lo = Math.min(0, min), hi = Math.max(0, max);
    const pos = (v) => ((v - lo) / (hi - lo || 1)) * 100;
    for (const r of rows) {
      const row = el('div', 'lp-row' + (r.selected ? ' sel' : ''));
      row.tabIndex = 0;
      row.append(el('span', 'lp-label', r.label));
      const track = el('div', 'lp-track');
      const zero = el('i', 'lp-zero');
      zero.style.left = pos(0) + '%';
      const bar = el('i', 'lp-bar');
      bar.style.left = Math.min(pos(0), pos(r.value)) + '%';
      bar.style.width = Math.abs(pos(r.value) - pos(0)) + '%';
      bar.style.background = r.color;
      const dot = el('i', 'lp-dot' + (r.hollow ? ' hollow' : ''));
      dot.style.left = pos(r.value) + '%';
      dot.style.background = r.color;
      dot.style.borderColor = r.color;
      track.append(zero, bar, dot);
      row.append(track, el('span', 'lp-val', r.text));
      if (r.tip) {
        const open = () => { const b = dot.getBoundingClientRect(); showTip(b.left + 5, b.top, r.tip.header, r.tip.rows); };
        row.addEventListener('pointerenter', open);
        row.addEventListener('focus', open);
        row.addEventListener('pointerleave', hideTip);
        row.addEventListener('blur', hideTip);
      }
      if (r.onClick) {
        row.style.cursor = 'pointer';
        row.setAttribute('role', 'button');
        if (r.selected != null) row.setAttribute('aria-pressed', String(!!r.selected));
        row.addEventListener('click', r.onClick);
        row.addEventListener('keydown', (ev) => {
          if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); r.onClick(); }
        });
      }
      host.append(row);
    }
  }

  function sparkline(values, stroke, dotColor, w = 84, h = 24) {
    const v = values.filter((x) => x != null);
    const root = svg('svg', { class: 'spark', viewBox: `0 0 ${w} ${h}`, 'aria-hidden': 'true', preserveAspectRatio: 'none' });
    if (v.length < 2) return root;
    const lo = Math.min(...v), hi = Math.max(...v), n = values.length;
    const X = (i) => 3 + (i / (n - 1)) * (w - 8);
    const Y = (y) => (hi === lo ? h / 2 : 3 + (1 - (y - lo) / (hi - lo)) * (h - 6));
    let d = '', started = false, last = null;
    values.forEach((y, i) => {
      if (y == null) return;
      d += `${started ? 'L' : 'M'}${X(i).toFixed(1)} ${Y(y).toFixed(1)}`;
      started = true; last = [X(i), Y(y)];
    });
    root.append(svg('path', { d, fill: 'none', stroke, 'stroke-width': 1.5, 'stroke-linejoin': 'round', 'vector-effect': 'non-scaling-stroke' }));
    root.append(svg('circle', { cx: last[0], cy: last[1], r: 2.5, fill: dotColor }));
    return root;
  }

  const legend = (host, entries) => {
    host.replaceChildren(...entries.map(([cls, color, label]) => {
      const s = el('span');
      const k = el('i', cls);
      if (cls === 'k-rect' || cls === 'k-dot' || cls === 'k-sq') k.style.background = color; else k.style.borderColor = color;
      if (cls === 'k-rect') k.style.opacity = 0.35;
      s.append(k, el('span', null, label));
      return s;
    }));
  };

  function dataTable(host, head, rows) {
    const table = el('table');
    const tr = el('tr');
    head.forEach((h, i) => { const th = el('th', i ? 'num' : null, h); th.scope = 'col'; tr.append(th); });
    const thead = el('thead'); thead.append(tr);
    const tbody = el('tbody');
    for (const r of rows) {
      const row = el('tr');
      r.forEach((c, i) => row.append(el('td', i ? 'num' : null, c)));
      tbody.append(row);
    }
    table.append(thead, tbody);
    host.replaceChildren(table);
  }

  // ------------------------------------------------------------------ sections
  function chgCell(v, extra = '') {
    const td = el('td', 'num ' + extra);
    if (v == null) { td.textContent = '–'; return td; }
    const flat = Math.abs(v) < 0.05;
    const s = el('span', 'chg ' + (flat ? 'flat' : v > 0 ? 'up' : 'down'));
    if (!flat) s.append(el('i', null, v > 0 ? '▲' : '▼'));
    s.append(document.createTextNode(flat ? pct(0, 0).replace('+', '') : pct(v).replace(/^[+−]/, '')));
    td.append(s);
    return td;
  }

  function renderHero() {
    const { app } = state;
    $('#hero-sub').textContent = t('hero_sub', { date: fmtDate(utc(app.meta.data_through)), n: num(app.meta.items) });
    const tiles = $('#tiles');
    tiles.replaceChildren();
    const tile = (label, value, sub, extra, href) => {
      const d = el(href ? 'a' : 'div', 'tile');
      if (href) d.href = href;
      d.append(el('div', 't-label', label), el('div', 't-value', value));
      if (sub) d.append(typeof sub === 'string' ? el('div', 't-sub', sub) : sub);
      if (extra) d.append(extra);
      tiles.append(d);
    };
    const last = app.basket.all[app.basket.all.length - 1];
    tile(t('tile_basket'), pct(last - 100, 0), t('tile_basket_sub', { v: num(last, 0) }),
      sparkline(app.basket.all, 'rgba(255,255,255,.75)', '#ffffff', 200, 26), '#trends');
    const moved = app.items.map((i) => i.chg.m1).filter((v) => v != null);
    const up = moved.filter((v) => v > 0.05).length, down = moved.filter((v) => v < -0.05).length;
    tile(t('tile_month'), num(up), t('tile_month_sub', { d: num(down), f: num(moved.length - up - down) }), null, '#prices');
    const live = app.items.filter((i) => i.spike);
    tile(t('tile_alert'), num(live.length), live.length ? live.map(name).join(', ') : t('tile_alert_none'), null, '#alerts');
    const ram = app.festivals.next.find((f) => f.festival === 'ramadan_start');
    if (ram) {
      const days = Math.max(0, Math.ceil((utc(ram.date) - Date.now()) / 864e5));
      tile(t('tile_ramadan'), t('days', { n: num(days) }),
        (ram.projected ? '~' : '') + fmtDate(utc(ram.date)) + (ram.projected ? ' · ' + t('projected') : ''),
        null, '#festivals');
    }
  }

  function renderChips() {
    const host = $('#chips');
    const mk = (id, label) => {
      const b = el('button', 'chip', label);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.cat === id));
      b.addEventListener('click', () => { state.cat = id; renderChips(); renderTable(); });
      return b;
    };
    host.replaceChildren(mk('all', t('all')), ...state.app.categories.map((c) => mk(c.id, catName(c.id))));
  }

  function renderTable() {
    const body = $('#price-body');
    const q = state.q.normalize('NFC').trim().toLowerCase();
    let rows = state.app.items.filter((i) => (state.cat === 'all' || i.cat === state.cat)
      && (!q || i.en.toLowerCase().includes(q) || i.bn.normalize('NFC').includes(q)));
    // unfiltered view starts with the 20-item core basket; any filter shows everything
    const collapsible = state.cat === 'all' && !q;
    const total = rows.length;
    if (collapsible && !state.showAllPrices) rows = rows.filter((i) => i.core);
    const more = $('#prices-more');
    more.hidden = !collapsible;
    more.textContent = state.showAllPrices ? t('show_core') : t('show_all', { n: num(total) });
    const m1 = (i) => i.chg.m1;
    if (state.sort === 'rise') rows.sort((a, b) => (m1(b) ?? -1e9) - (m1(a) ?? -1e9));
    if (state.sort === 'fall') rows.sort((a, b) => (m1(a) ?? 1e9) - (m1(b) ?? 1e9));
    if (state.sort === 'name') rows.sort((a, b) => name(a).localeCompare(name(b), loc()));
    body.replaceChildren();
    let lastCat = null;
    for (const it of rows) {
      if (state.sort === 'cat' && it.cat !== lastCat) {
        lastCat = it.cat;
        const tr = el('tr', 'cat-row');
        const td = el('td', null, catName(it.cat));
        td.colSpan = 6;
        tr.append(td);
        body.append(tr);
      }
      const tr = el('tr');
      const td = el('td');
      const btn = el('button', 'i-name', name(it));
      btn.type = 'button';
      btn.style.cssText = 'background:none;border:0;padding:0;text-align:left;cursor:pointer';
      td.append(btn);
      if (it.spike) td.append(el('span', 'badge', t('jump')));
      td.append(el('div', 'i-unit', t('per', { u: unit(it) })));
      const pr = el('td', 'num', span(it.min, it.max).replace('৳', ''));
      const sp = el('td', 'hide-s');
      sp.append(sparkline(it.spark, css('--muted'), css('--s1')));
      tr.append(td, pr, chgCell(it.chg.w1, 'hide-s'), chgCell(it.chg.m1), chgCell(it.chg.y1, 'hide-s'), sp);
      tr.addEventListener('click', () => openDetail(it.id));
      body.append(tr);
    }
    $('#price-empty').hidden = rows.length > 0;
  }

  function renderAlerts() {
    const { app } = state;
    $('#alerts-sub').textContent = t('alerts_sub', {
      r: app.spike_recall.replace(/\D*(\d+)\/(\d+).*/, (_, a, b) => `${num(+a)}/${num(+b)}`) });
    const grid = $('#alert-grid');
    const liveIds = new Set(app.items.filter((i) => i.spike).map((i) => i.id));
    const all = app.spikes.filter((s) => itemById(s.id));
    const shown = state.showAllAlerts ? all : all.slice(0, 8);
    grid.replaceChildren(...shown.map((s, i) => {
      const it = itemById(s.id);
      const b = el('button', 'alert');
      b.type = 'button';
      if (i === all.findIndex((x) => x.id === s.id) && liveIds.has(s.id)) b.append(el('span', 'live', t('active')));
      b.append(el('div', 'a-name', name(it)));
      const p = el('div', 'a-pct');
      p.append(el('i', null, '▲'), document.createTextNode(pct(s.pct, 0).replace('+', '')), el('span', 'a-meta', t('in2w')));
      b.append(p, el('div', 'a-meta', `${taka(s.before)} → ${taka(s.peak)} · ${fmtDate(utc(s.start), { day: 'numeric', month: 'short', year: 'numeric' })}`));
      b.addEventListener('click', () => openDetail(s.id));
      return b;
    }));
    const more = $('#alerts-more');
    more.hidden = all.length <= 8;
    more.textContent = state.showAllAlerts ? t('show_less') : t('show_all', { n: num(all.length) });
  }

  function renderTrends() {
    const { app } = state;
    const b = app.basket;
    const ts = b.months.map((m) => utc(m + '-01'));
    const imp = b.imp.map((v, i) => [ts[i], v]).filter((p) => p[1] != null);
    const dom = b.dom.map((v, i) => [ts[i], v]).filter((p) => p[1] != null);
    $('#basket-title').textContent = t('basket_title', {
      imp: pct(imp[imp.length - 1][1] - 100, 0), dom: pct(dom[dom.length - 1][1] - 100, 0) });
    legend($('#basket-legend'), [['k-line', css('--s1'), t('imp')], ['k-line', css('--s2'), t('dom')]]);
    lineChart($('#basket-chart'), {
      label: $('#basket-title').textContent, endLabels: true, yFmt: (v) => num(v, 0),
      lines: [{ label: t('imp'), color: css('--s1'), pts: imp }, { label: t('dom'), color: css('--s2'), pts: dom }],
      tip: (tv) => ({
        header: fmtDate(tv, { month: 'long', year: 'numeric' }),
        rows: [[imp, '--s1', 'imp'], [dom, '--s2', 'dom']].map(([arr, c, k]) => {
          const p = arr.find((q) => q[0] === tv);
          return p && { color: css(c), value: num(p[1], 1), label: t(k) };
        }).filter(Boolean),
      }),
    });
    dataTable($('#basket-table'), [t('month'), t('imp'), t('dom'), t('all_items')],
      b.months.map((m, i) => [fmtDate(ts[i], { month: 'short', year: 'numeric' }),
        b.imp[i] == null ? '–' : num(b.imp[i], 1), b.dom[i] == null ? '–' : num(b.dom[i], 1),
        b.all[i] == null ? '–' : num(b.all[i], 1)]).reverse());

    const color = { 'import-dependent': css('--s1'), domestic: css('--s2'), other: css('--context') };
    const label = { 'import-dependent': t('imp'), domestic: t('dom'), other: t('other') };
    const rows = app.items.filter((i) => i.since_base != null).sort((a, c) => c.since_base - a.since_base);
    legend($('#items-legend'), [['k-dot', color['import-dependent'], t('imp')],
      ['k-dot', color.domestic, t('dom')], ['k-dot', color.other, t('other')]]);
    const shown = state.showAllItems ? rows : rows.slice(0, 12);
    lollipop($('#items-chart'), shown.map((i) => ({
      label: name(i), value: i.since_base, text: pct(i.since_base, 0), color: color[i.supply],
      tip: { header: name(i), rows: [{ color: color[i.supply], value: pct(i.since_base, 0), label: label[i.supply] }] },
      onClick: () => openDetail(i.id),
    })), { min: Math.min(...rows.map((r) => r.since_base)), max: Math.max(...rows.map((r) => r.since_base)) });
    $('#items-more').textContent = state.showAllItems ? t('show_less') : t('show_all', { n: num(rows.length) });
  }

  function renderFestivals() {
    const f = state.app.festivals;
    $('#countdown').replaceChildren(...f.next.map((n) => {
      const d = el('div', 'cd');
      const days = Math.max(0, Math.ceil((utc(n.date) - Date.now()) / 864e5));
      d.append(el('span', null, t(n.festival)), el('b', null, t('days', { n: num(days) })),
        el('span', null, (n.projected ? '~' : '') + fmtDate(utc(n.date)) + (n.projected ? ' · ' + t('projected') : '')));
      return d;
    }));
    $('#fest-seg').replaceChildren(...['ramadan_start', 'eid_ul_fitr', 'eid_ul_adha'].map((k) => {
      const b = el('button', null, t(k));
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.fest === k));
      b.addEventListener('click', () => { state.fest = k; renderFestivals(); });
      return b;
    }));
    legend($('#fest-legend'), [['k-dot', css('--up'), t('pricier')], ['k-dot', css('--down'), t('cheaper')],
      ['k-dot', css('--ink2'), t('clear')], ['k-ring', css('--ink2'), t('unclear')]]);
    const all = f.effects.map((e) => e.pct);
    const rows = f.items.map((id) => f.effects.find((e) => e.id === id && e.festival === state.fest))
      .filter((e) => e && itemById(e.id));
    const paths = (f.paths && f.paths[state.fest]) || {};
    const pathItem = state.festItem && paths[state.festItem] ? state.festItem
      : (rows.find((e) => e.sig && paths[e.id]) || rows.find((e) => paths[e.id]) || {}).id;
    lollipop($('#fest-chart'), rows.map((e) => {
      const c = css(e.pct >= 0 ? '--up' : '--down');
      return { label: name(itemById(e.id)), value: e.pct, text: pct(e.pct), color: c, hollow: !e.sig,
        selected: e.id === pathItem, onClick: () => { state.festItem = e.id; renderFestivals(); },
        tip: { header: `${name(itemById(e.id))} · ${t(state.fest)}`,
          rows: [{ color: c, value: pct(e.pct), label: t(e.sig ? 'clear' : 'unclear') },
            { value: '', label: t('fest_tip', { a: num(e.above), y: num(e.years) }) }] } };
    }), { min: Math.min(...all), max: Math.max(...all) });
    renderPath(pathItem);
  }

  function renderForecast() {
    const fc = state.app.forecast;
    $('#forecast').hidden = !fc;
    if (!fc) return;
    $('#fc-sub').textContent = t('fc_sub', { n: num(fc.scored) });
    const order = ['ses', 'gbm_median', 'drift', 'gbm', 'seasonal'];
    const rows = order.map((mdl) => fc.point.find((p) => p.h === 4 && p.model === mdl)).filter(Boolean);
    lollipop($('#models-chart'), rows.map((p) => {
      const v = (p.rel - 1) * 100;
      return { label: t('m_' + p.model), value: v, text: pct(v, 0), color: css('--s1'),
        tip: { header: t('m_' + p.model), rows: [{ color: css('--s1'), value: pct(v, 1), label: t('worse') }] } };
    }), { min: 0, max: Math.max(...rows.map((p) => (p.rel - 1) * 100)) });
    $('#cov-tiles').replaceChildren(...fc.intervals.filter((i) => i.method === fc.method).map((i) => {
      const d = el('div', 'mini');
      d.append(el('b', null, num(i.cov, 1) + '%'), el('span', null, t('wk', { h: num(i.h) })));
      return d;
    }));
    const typ = fc.naive_mae.find((x) => x.h === 4);
    $('#fc-typical').textContent = typ ? t('fc_typical', { p: num(typ.pct, 1) }) : '';
  }

  // ------------------------------------------------------------------ helpers for the new views
  const toastEl = $('#toast');
  let toastTimer = null;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { toastEl.hidden = true; }, 2200);
  }
  function shareUrl(id) {
    const q = new URLSearchParams({ item: id });
    if (state.lang === 'bn') q.set('lang', 'bn');
    return `${location.origin}${location.pathname}?${q}`;
  }
  function setUrlItem(id) {
    try {
      const q = new URLSearchParams(location.search);
      if (id) q.set('item', id); else q.delete('item');
      const qs = q.toString();
      history.replaceState(null, '', location.pathname + (qs ? '?' + qs : '') + location.hash);
    } catch { /* ignore */ }
  }
  const signedTaka = (d) => (d > 0.5 ? '+' : d < -0.5 ? '−' : '') + '৳' + price(Math.abs(Math.round(d)));
  const monthName = (m, style = 'long') => fmtDate(Date.UTC(2021, m, 1), { month: style });
  function mix(a, b, w) {
    const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
    const A = p(a), B = p(b);
    return '#' + A.map((v, i) => Math.round(v + (B[i] - v) * w).toString(16).padStart(2, '0')).join('');
  }
  function itemSelect(sel, placeholder, exclude, disabled) {
    sel.replaceChildren();
    const first = el('option', null, placeholder);
    first.value = '';
    sel.append(first);
    for (const c of state.app.categories) {
      const og = document.createElement('optgroup');
      og.label = catName(c.id);
      for (const it of state.app.items) {
        if (it.cat !== c.id || exclude.includes(it.id)) continue;
        const o = el('option', null, name(it));
        o.value = it.id;
        og.append(o);
      }
      if (og.children.length) sel.append(og);
    }
    sel.value = '';
    sel.disabled = !!disabled;
    sel.classList.add('add');
  }

  // ------------------------------------------------------------------ my bazaar
  const BASKET_DEFAULT = [['rice_coarse', 30], ['atta_loose', 4], ['soybean_loose', 4], ['lentil_bold', 2],
    ['potato', 6], ['onion_local', 3], ['eggs', 6], ['chicken_broiler', 3], ['sugar', 2], ['rui', 2]];
  function loadBasket() {
    try {
      const saved = JSON.parse(localStorage.getItem('pp-basket'));
      if (Array.isArray(saved)) return saved.filter((r) => Array.isArray(r) && itemById(r[0]) && r[1] >= 0);
    } catch { /* storage unavailable or corrupt: fall back to the example */ }
    return BASKET_DEFAULT.map((r) => [...r]).filter(([id]) => itemById(id));
  }
  function saveBasket() {
    try { localStorage.setItem('pp-basket', JSON.stringify(state.basket)); } catch { /* ignore */ }
  }
  function renderBasket(rebuild) {
    if (!state.basket) state.basket = loadBasket();
    if (rebuild) {
      const body = $('#b-body');
      body.replaceChildren();
      for (const row of state.basket) {
        const it = itemById(row[0]);
        const tr = el('tr');
        const c1 = el('td');
        const nb = el('button', 'i-name', name(it));
        nb.type = 'button';
        nb.style.cssText = 'background:none;border:0;padding:0;text-align:left;cursor:pointer';
        nb.addEventListener('click', () => openDetail(it.id));
        c1.append(nb, el('div', 'i-unit', `${taka(it.mid)} · ${t('per', { u: unit(it) })}`));
        const c2 = el('td', 'num');
        const box = el('span', 'qty');
        const minus = el('button', null, '−');
        const plus = el('button', null, '+');
        const inp = el('input');
        minus.type = 'button';
        plus.type = 'button';
        minus.setAttribute('aria-label', t('less', { x: name(it) }));
        plus.setAttribute('aria-label', t('more_of', { x: name(it) }));
        inp.type = 'number'; inp.min = '0'; inp.step = '0.5'; inp.inputMode = 'decimal';
        inp.value = String(row[1]);
        inp.setAttribute('aria-label', t('qty_of', { x: name(it) }));
        const c3 = el('td', 'num', taka(Math.round(row[1] * it.mid)));
        const set = (v) => {
          row[1] = Math.max(0, Math.round((Number.isFinite(v) ? v : 0) * 2) / 2);
          inp.value = String(row[1]);
          c3.textContent = taka(Math.round(row[1] * it.mid));
          saveBasket();
          renderBasketResult();
        };
        minus.addEventListener('click', () => set(row[1] - 1));
        plus.addEventListener('click', () => set(row[1] + 1));
        inp.addEventListener('change', () => set(parseFloat(inp.value)));
        box.append(minus, inp, plus);
        c2.append(box);
        const c4 = el('td');
        const rm = el('button', 'rm', '×');
        rm.type = 'button';
        rm.setAttribute('aria-label', t('remove', { x: name(it) }));
        rm.addEventListener('click', () => {
          state.basket = state.basket.filter((r) => r !== row);
          saveBasket(); renderBasket(true);
        });
        c4.append(rm);
        tr.append(c1, c2, c3, c4);
        body.append(tr);
      }
      $('#b-empty').hidden = state.basket.length > 0;
      itemSelect($('#b-add'), t('b_add'), state.basket.map((r) => r[0]));
    }
    renderBasketResult();
  }

  function renderBasketResult() {
    const rows = state.basket.map(([id, q]) => {
      const it = itemById(id);
      const now = q * it.mid;
      const back = (c) => (c == null ? null : now / (1 + c / 100));
      return { it, q, now, m1: back(it.chg.m1), y1: back(it.chg.y1) };
    }).filter((r) => r.q > 0);
    const sum = (arr, k) => arr.reduce((a, r) => a + r[k], 0);
    const total = sum(rows, 'now');
    const tiles = $('#b-tiles');
    tiles.replaceChildren();
    const tile = (label, big, small, dir) => {
      const d = el('div', 'b-tile');
      d.append(el('span', null, label));
      d.append(el('b', dir ? (dir > 0 ? 'delta-up' : 'delta-down') : null, big));
      if (small) d.append(el('i', null, small));
      tiles.append(d);
    };
    tile(t('b_total'), taka(Math.round(total)));
    for (const [k, label] of [['m1', 'b_vs_m'], ['y1', 'b_vs_y']]) {
      const ok = rows.filter((r) => r[k] != null);
      const now = sum(ok, 'now'), then = sum(ok, k);
      const d = now - then;
      tile(t(label), ok.length ? signedTaka(d) : '–', ok.length && then ? pct((now / then - 1) * 100) : '',
        Math.abs(d) < 0.5 ? 0 : Math.sign(d));
    }

    // where the money goes: tall segmented bar, top 5 + other
    const seg = $('#b-seg');
    const sorted = [...rows].sort((a, b) => b.now - a.now);
    const parts = sorted.slice(0, 5).map((r, i) => ({ label: name(r.it), v: r.now, color: css('--s' + (i + 1)), dark: i === 3 }));
    const rest = sorted.slice(5).reduce((a, r) => a + r.now, 0);
    // grey "Other" takes dark text on the light theme's pale grey, white on the dark theme's deep grey
    const darkTheme = matchMedia('(prefers-color-scheme: dark)').matches;
    if (rest > 0) parts.push({ label: t('other'), v: rest, color: css('--context'), dark: !darkTheme });
    seg.replaceChildren(...parts.map((p) => {
      const share = total ? (p.v / total) * 100 : 0;
      const d = el('div', p.dark ? 'dark-text' : null, share >= 9 ? num(share, 0) + '%' : '');
      d.style.flex = `${p.v} 1 0`;
      d.style.background = p.color;
      d.tabIndex = 0;
      const open = () => {
        const b = d.getBoundingClientRect();
        showTip(b.left + b.width / 2, b.top, p.label, [{ value: taka(Math.round(p.v)), label: num(share, 0) + '%' }]);
      };
      d.addEventListener('pointerenter', open);
      d.addEventListener('focus', open);
      d.addEventListener('pointerleave', hideTip);
      d.addEventListener('blur', hideTip);
      return d;
    }));
    seg.setAttribute('aria-label', parts.map((p) => `${p.label} ${num(total ? (p.v / total) * 100 : 0, 0)}%`).join(', '));
    legend($('#b-seg-legend'), parts.map((p) => ['k-sq', p.color, p.label]));

    // what changed the bill since last year
    const drv = rows.filter((r) => r.y1 != null).map((r) => ({ r, d: r.now - r.y1 }))
      .sort((a, b) => Math.abs(b.d) - Math.abs(a.d)).slice(0, 8);
    const vals = drv.map((x) => x.d);
    lollipop($('#b-drivers'), drv.map(({ r, d }) => ({
      label: name(r.it), value: d, text: signedTaka(d), color: css(d >= 0 ? '--up' : '--down'),
      tip: { header: name(r.it), rows: [{ value: `${taka(Math.round(r.y1))} → ${taka(Math.round(r.now))}`,
        label: `${t('year_ago')} → ${t('b_total')}` }] },
      onClick: () => openDetail(r.it.id),
    })), { min: Math.min(0, ...vals), max: Math.max(0, ...vals) });
    const missing = rows.filter((r) => r.y1 == null).length;
    $('#b-note').textContent = (missing ? t('b_excluded', { n: num(missing) }) + ' ' : '') + t('b_src');
  }

  // ------------------------------------------------------------------ compare
  function renderCompare() {
    const M = state.app.monthly;
    state.compare = state.compare.filter((id) => M.v[id] && itemById(id));
    for (const id of Object.keys(state.cmpSlot)) if (!state.compare.includes(id)) delete state.cmpSlot[id];
    for (const id of state.compare) {
      if (state.cmpSlot[id] != null) continue;
      const used = new Set(Object.values(state.cmpSlot));
      let k = 0;
      while (used.has(k)) k++;
      state.cmpSlot[id] = k; // colour follows the item, never its position in the list
    }
    itemSelect($('#cmp-add'), t('cmp_add'), state.compare, state.compare.length >= 4);
    $('#cmp-period').replaceChildren(...['base', '3y', '1y'].map((k) => {
      const b = el('button', null, t('p_' + k));
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.cmpPeriod === k));
      b.addEventListener('click', () => { state.cmpPeriod = k; renderCompare(); });
      return b;
    }));
    const n = M.months.length;
    const start = state.cmpPeriod === 'base' ? Math.max(0, M.months.indexOf('2020-07'))
      : Math.max(0, n - (state.cmpPeriod === '3y' ? 37 : 13));
    const months = M.months.slice(start);
    const ts = months.map((m) => utc(m + '-01'));
    const lines = state.compare.map((id) => {
      const v = M.v[id].slice(start);
      const base = v.find((x) => x != null);
      return { id, label: name(itemById(id)), color: css('--s' + (state.cmpSlot[id] + 1)),
        pts: v.map((x, i) => (x == null ? null : [ts[i], (x / base) * 100])).filter(Boolean) };
    }).filter((l) => l.pts.length > 1);

    $('#cmp-legend').replaceChildren(...lines.map((l) => {
      const s = el('span', 'rm-key');
      const k = el('i', 'k-line');
      k.style.borderColor = l.color;
      const x = el('button', null, '×');
      x.type = 'button';
      x.setAttribute('aria-label', t('remove', { x: l.label }));
      x.addEventListener('click', () => { state.compare = state.compare.filter((id) => id !== l.id); renderCompare(); });
      s.append(k, el('span', null, l.label), x);
      return s;
    }));
    const host = $('#cmp-chart');
    if (!lines.length) {
      host._ro?.disconnect();
      host.replaceChildren(el('p', 'empty', t('cmp_none')));
      $('#cmp-table').replaceChildren();
      return;
    }
    lineChart(host, {
      label: t('cmp_title'), endLabels: true, yFmt: (v) => num(v, 0), lines,
      xFmt: (tv) => fmtDate(tv, { month: 'long', year: 'numeric' }),
      tip: (tv) => {
        const i = ts.indexOf(tv);
        return { header: fmtDate(tv, { month: 'long', year: 'numeric' }),
          rows: lines.map((l) => {
            const p = l.pts.find((q) => q[0] === tv);
            return p && { color: l.color, value: num(p[1], 0), label: `${l.label} · ${taka(M.v[l.id][start + i])}` };
          }).filter(Boolean) };
      },
    });
    dataTable($('#cmp-table'), [t('month'), ...lines.map((l) => l.label)],
      months.map((m, i) => [fmtDate(ts[i], { month: 'short', year: 'numeric' }),
        ...lines.map((l) => { const v = M.v[l.id][start + i]; return v == null ? '–' : price(v); })]).reverse());
  }

  // ------------------------------------------------------------------ heatmap
  function heatColor(v) {
    const end = css(v >= 0 ? '--div-up' : '--div-down');
    return mix(css('--div-mid'), end, Math.pow(Math.min(1, Math.abs(v) / 15), 0.7));
  }
  function renderHeat() {
    const M = state.app.monthly;
    const ids = state.app.items.filter((i) => i.core && M.v[i.id]).map((i) => i.id);
    const N = innerWidth < 640 ? 12 : 24;
    const n = M.months.length;
    const idx = Array.from({ length: N }, (_, j) => n - N + j);
    const grid = $('#heat');
    grid.style.gridTemplateColumns = `minmax(92px, 170px) repeat(${N}, minmax(12px, 1fr))`;
    const cells = [el('div')];
    for (const i of idx) {
      const [y, m] = M.months[i].split('-').map(Number);
      const lab = m === 1 ? fmtDate(Date.UTC(y, 0, 1), { month: 'short', year: '2-digit' })
        : (m - 1) % 3 === 0 ? monthName(m - 1, 'short') : '';
      cells.push(el('div', 'hm', lab));
    }
    const change = (id, i) => {
      const v = M.v[id], a = v[i], b = v[i - 1];
      return a != null && b != null ? (a / b - 1) * 100 : null;
    };
    for (const id of ids) {
      const it = itemById(id);
      cells.push(el('div', 'hl', name(it)));
      for (const i of idx) {
        const ch = change(id, i);
        const c = el('div', 'c' + (ch == null ? ' na' : ''));
        if (ch != null) {
          c.style.background = heatColor(ch);
          const [y, m] = M.months[i].split('-').map(Number);
          const header = `${name(it)} · ${fmtDate(Date.UTC(y, m - 1, 1), { month: 'long', year: 'numeric' })}`;
          c.addEventListener('pointerenter', () => {
            const b = c.getBoundingClientRect();
            showTip(b.left + b.width / 2, b.top, header, [{ color: c.style.background, value: pct(ch), label: t('heat_tip') }]);
          });
          c.addEventListener('pointerleave', hideTip);
          c.addEventListener('click', () => openDetail(id));
        }
        cells.push(c);
      }
    }
    grid.replaceChildren(...cells);
    const bar = el('span', 'bar');
    bar.style.background = `linear-gradient(90deg, ${css('--div-down')}, ${css('--div-mid')}, ${css('--div-up')})`;
    $('#heat-legend').replaceChildren(el('span', null, `${pct(-15, 0)} ${t('heat_cheaper')}`), bar,
      el('span', null, `${pct(15, 0)} ${t('heat_pricier')}`));
    dataTable($('#heat-table'), [t('col_item'), ...idx.map((i) => fmtDate(utc(M.months[i] + '-01'), { month: 'short', year: '2-digit' }))],
      ids.map((id) => [name(itemById(id)), ...idx.map((i) => { const ch = change(id, i); return ch == null ? '–' : pct(ch); })]));
  }

  // ------------------------------------------------------------------ festival path
  function renderPath(id) {
    const f = state.app.festivals;
    const P = id && f.paths && f.paths[state.fest] && f.paths[state.fest][id];
    const box = $('.path-box');
    box.hidden = !P;
    if (!P) return;
    const fest = t(state.fest);
    $('#path-title').textContent = t('path_title', { f: fest, item: name(itemById(id)) });
    $('#path-sub').textContent = t('path_sub', { n: num(P.n) });
    const c = css('--s1');
    legend($('#path-legend'), [['k-line', c, t('avg')], ['k-rect', c, t('range_years')]]);
    const days = f.paths.days;
    const mean = days.map((d, i) => [d, P.mean[i]]).filter((p) => p[1] != null);
    const band = days.map((d, i) => [d, P.lo[i], P.hi[i]]).filter((p) => p[1] != null && p[2] != null);
    const dayFmt = (d) => (d === 0 ? t('day0', { f: fest })
      : t(d < 0 ? 'days_before' : 'days_after', { n: num(Math.abs(d)) }));
    lineChart($('#path-chart'), {
      label: $('#path-title').textContent, yFmt: (v) => pct(v, 0),
      lines: [{ label: t('avg'), color: c, pts: mean }], band: { color: c, pts: band },
      markers: [{ x: 0, label: fest }], xFmt: dayFmt,
      xTicks: (t0, t1) => [-60, -30, 0, 30].filter((d) => d >= t0 && d <= t1)
        .map((d) => ({ t: d, label: d === 0 ? num(0) : (d > 0 ? '+' : '−') + num(Math.abs(d)) + t('d_short') })),
      tip: (tv) => {
        const i = days.indexOf(tv);
        return { header: dayFmt(tv), rows: [{ color: c, value: pct(P.mean[i]), label: t('avg') },
          { value: `${pct(P.lo[i])} … ${pct(P.hi[i])}`, label: t('range_years') }] };
      },
    });
  }

  // ------------------------------------------------------------------ a typical year (item view)
  function renderSeason(it) {
    const box = $('#d-season');
    box.replaceChildren(el('h3', null, t('season_title')));
    const s = it.season;
    if (!s) { box.append(el('p', 'sub', t('season_none'))); return; }
    const lo = s.pct.indexOf(Math.min(...s.pct)), hi = s.pct.indexOf(Math.max(...s.pct));
    const sentence = s.amp < 5 ? t('season_flat', { amp: num(s.amp, 0) })
      : t('season_txt', { lo: monthName(lo), hi: monthName(hi), amp: num(s.amp, 0), n: num(s.years) });
    box.append(el('p', 'sub', sentence));
    const host = el('div', 'season');
    box.append(host);
    const draw = () => {
      const W = host.clientWidth, H = host.clientHeight;
      if (!W) return;
      const m = { l: 40, r: 4, t: 8, b: 20 };
      const pw = W - m.l - m.r, ph = H - m.t - m.b;
      const A = Math.max(2, ...s.pct.map(Math.abs)) * 1.1;
      const Y = (v) => m.t + (1 - (v + A) / (2 * A)) * ph;
      const band = pw / 12, bw = Math.min(24, band * 0.62);
      const root = svg('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': sentence });
      for (const v of [-A / 1.1, 0, A / 1.1]) {
        root.append(svg('line', { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: css(v ? '--grid' : '--axis'), 'stroke-width': 1 }));
        const tx = svg('text', { x: m.l - 6, y: Y(v) + 4, 'text-anchor': 'end' });
        tx.textContent = pct(v, 0);
        root.append(tx);
      }
      s.pct.forEach((v, i) => {
        const x = m.l + i * band + (band - bw) / 2;
        const y0 = Y(0), y1 = Y(v);
        const r = Math.min(4, Math.abs(y1 - y0) / 2, bw / 2);
        const up = v >= 0;
        // 4px rounded data end, square at the zero baseline
        const d = up
          ? `M${x} ${y0}V${y1 + r}Q${x} ${y1} ${x + r} ${y1}H${x + bw - r}Q${x + bw} ${y1} ${x + bw} ${y1 + r}V${y0}Z`
          : `M${x} ${y0}V${y1 - r}Q${x} ${y1} ${x + r} ${y1}H${x + bw - r}Q${x + bw} ${y1} ${x + bw} ${y1 - r}V${y0}Z`;
        root.append(svg('path', { d, fill: css(up ? '--up' : '--down'), opacity: i === lo || i === hi ? 1 : 0.55 }));
        if (band >= 26 || i % 2 === 0) {
          const tx = svg('text', { x: x + bw / 2, y: H - 5, 'text-anchor': 'middle' });
          tx.textContent = monthName(i, 'short');
          root.append(tx);
        }
        const hit = svg('rect', { x: m.l + i * band, y: m.t, width: band, height: ph, fill: 'transparent' });
        hit.addEventListener('pointerenter', () => {
          const b = hit.getBoundingClientRect();
          showTip(b.left + b.width / 2, b.top + 10, monthName(i), [{ color: css(up ? '--up' : '--down'), value: pct(v), label: t('vs_avg') }]);
        });
        hit.addEventListener('pointerleave', hideTip);
        root.append(hit);
      });
      host.replaceChildren(root);
    };
    new ResizeObserver(draw).observe(host);
    draw();
  }

  // ------------------------------------------------------------------ detail dialog
  const dialog = $('#detail');
  async function loadSeries(id) {
    if (!state.series.has(id)) {
      const res = await fetch(`data/series/${id}.json`);
      if (!res.ok) throw new Error('series ' + res.status);
      const s = await res.json();
      const e = utc(s.epoch);
      state.series.set(id, s.d.map((d, i) => [e + d * 864e5, s.lo[i], s.hi[i]]));
    }
    return state.series.get(id);
  }

  function renderDetail() {
    const it = state.item;
    if (!it) return;
    $('#d-title').textContent = name(it);
    $('#d-unit').textContent = `${t('per', { u: unit(it) })} · ${catName(it.cat)}`;
    const stats = $('#d-stats');
    const stat = (label, node) => { const d = el('div', 'd-stat'); d.append(el('span', null, label)); d.append(node); stats.append(d); };
    stats.replaceChildren();
    stat(t('now'), el('b', null, span(it.min, it.max)));
    for (const [k, lab] of [['w1', 'col_w1'], ['m1', 'col_m1'], ['y1', 'col_y1']]) {
      const b = el('b');
      const cell = chgCell(it.chg[k]);
      b.append(...cell.childNodes);
      stat(t(lab), b);
    }
    $('#d-range').replaceChildren(...['r3m', 'r1y', 'rall'].map((k) => {
      const b = el('button', null, t(k));
      b.type = 'button';
      b.setAttribute('aria-pressed', String(state.range === k));
      b.addEventListener('click', () => { state.range = k; renderDetail(); });
      return b;
    }));
    const c1 = css('--s1');
    const entries = [['k-line', c1, t('k_mid')], ['k-rect', c1, t('k_band')]];
    if (it.fc) entries.push(['k-rect', c1, t('k_cone')], ['k-dots', c1, t('k_today')]);
    legend($('#d-legend'), entries);

    const fcBox = $('#d-forecast');
    fcBox.replaceChildren();
    const box = el('div', 'fc-box');
    if (it.fc) {
      box.append(el('h3', null, t('next4')));
      const grid = el('div', 'fc-grid');
      for (const f of it.fc) {
        const cell = el('div', 'fc-cell');
        cell.append(el('span', null, fmtDate(utc(f.date), { day: 'numeric', month: 'short' })), el('b', null, span(f.lo, f.hi)));
        grid.append(cell);
      }
      box.append(grid);
      if (it.cov != null) box.append(el('p', 'note', t('fc_cov', { p: num(it.cov) })));
    } else {
      box.append(el('p', 'sub', t('fc_none')));
    }
    fcBox.append(box);

    renderSeason(it);
    const all = state.series.get(it.id);
    if (!all) return;
    const end = all[all.length - 1][0];
    const from = state.range === 'r3m' ? end - 92 * 864e5 : state.range === 'r1y' ? end - 366 * 864e5 : -Infinity;
    const pts = all.filter((p) => p[0] >= from);
    const mid = pts.map((p) => [p[0], (p[1] + p[2]) / 2]);
    const cfg = {
      label: name(it), yFmt: (v) => price(Math.round(v * 10) / 10),
      band: { color: c1, pts },
      lines: [{ label: t('k_mid'), color: c1, pts: mid }],
    };
    let cone = null;
    if (it.fc) {
      const now = mid[mid.length - 1];
      cone = [[now[0], now[1], now[1]], ...it.fc.map((f) => [utc(f.date), f.lo, f.hi])];
      cfg.cone = { color: c1, pts: cone };
      cfg.lines.push({ label: t('k_today'), color: c1, dotted: true, pts: cone.map((p) => [p[0], now[1]]) });
    }
    cfg.tip = (tv) => {
      const h = pts.find((p) => p[0] === tv);
      if (h) return { header: fmtDate(tv), rows: [
        { color: c1, value: taka((h[1] + h[2]) / 2), label: t('k_mid') },
        { value: span(h[1], h[2]), label: t('k_band') }] };
      const f = cone?.find((p) => p[0] === tv);
      return { header: fmtDate(tv), rows: f ? [{ color: c1, value: span(f[1], f[2]), label: t('k_cone') }] : [] };
    };
    lineChart($('#d-chart'), cfg);
    dataTable($('#d-table'), [t('date'), t('low'), t('high')],
      all.slice(-40).reverse().map((p) => [fmtDate(p[0]), price(p[1]), price(p[2])]));
  }

  async function openDetail(id) {
    state.item = itemById(id);
    if (!state.item) return;
    hideTip();
    $('#d-chart').replaceChildren();
    renderDetail();
    if (!dialog.open) dialog.showModal();
    dialog.append(tip, toastEl); // the dialog is in the top layer; overlays must live inside it
    setUrlItem(id);
    try { await loadSeries(id); if (state.item?.id === id) renderDetail(); }
    catch (err) { $('#d-chart').replaceChildren(el('p', 'empty', t('load_fail'))); }
  }
  dialog.addEventListener('close', () => {
    document.body.append(tip, toastEl); hideTip(); state.item = null; setUrlItem(null);
  });
  $('#d-share').addEventListener('click', async () => {
    if (!state.item) return;
    const url = shareUrl(state.item.id);
    try {
      if (navigator.share) { await navigator.share({ title: `${name(state.item)} — PricePulse BD`, url }); return; }
    } catch (err) { if (err && err.name === 'AbortError') return; }
    try { await navigator.clipboard.writeText(url); toast(t('copied')); } catch { toast(url); }
  });
  dialog.addEventListener('click', (ev) => { if (ev.target === dialog) dialog.close(); });
  $('#d-close').addEventListener('click', () => dialog.close());

  // ------------------------------------------------------------------ wiring
  function applyStatic() {
    document.documentElement.lang = state.lang;
    document.title = `PricePulse BD — ${t('headline')}`;
    for (const n of document.querySelectorAll('[data-i18n]')) n.textContent = t(n.dataset.i18n);
    for (const n of document.querySelectorAll('[data-i18n-aria]')) n.setAttribute('aria-label', t(n.dataset.i18nAria));
    for (const n of document.querySelectorAll('[data-i18n-placeholder]')) {
      n.placeholder = t(n.dataset.i18nPlaceholder);
      n.setAttribute('aria-label', n.placeholder);
    }
    for (const b of document.querySelectorAll('.lang button')) b.setAttribute('aria-pressed', String(b.dataset.lang === state.lang));
    $('#foot-updated').textContent = t('foot_updated', { date: fmtDate(utc(state.app.meta.data_through)) });
  }

  function renderAll() {
    applyStatic();
    renderHero(); renderChips(); renderTable(); renderBasket(true); renderAlerts(); renderTrends();
    renderCompare(); renderHeat(); renderFestivals(); renderForecast();
    if (state.item) renderDetail();
  }

  for (const b of document.querySelectorAll('.lang button')) {
    b.addEventListener('click', () => {
      state.lang = b.dataset.lang;
      try { localStorage.setItem('pp-lang', state.lang); } catch { /* ignore */ }
      renderAll();
    });
  }
  $('#search').addEventListener('input', (ev) => { state.q = ev.target.value; renderTable(); });
  $('#sort').addEventListener('change', (ev) => { state.sort = ev.target.value; renderTable(); });
  $('#prices-more').addEventListener('click', () => { state.showAllPrices = !state.showAllPrices; renderTable(); });
  $('#alerts-more').addEventListener('click', () => { state.showAllAlerts = !state.showAllAlerts; renderAlerts(); });
  $('#items-more').addEventListener('click', () => { state.showAllItems = !state.showAllItems; renderTrends(); });
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => state.app && renderAll());
  matchMedia('(max-width: 639px)').addEventListener('change', () => state.app && renderHeat());
  $('#b-add').addEventListener('change', (ev) => {
    const id = ev.target.value;
    if (id && !state.basket.some((r) => r[0] === id)) { state.basket.push([id, 1]); saveBasket(); }
    renderBasket(true);
  });
  $('#b-reset').addEventListener('click', () => {
    state.basket = BASKET_DEFAULT.map((r) => [...r]).filter(([id]) => itemById(id));
    saveBasket(); renderBasket(true);
  });
  $('#cmp-add').addEventListener('change', (ev) => {
    const id = ev.target.value;
    if (id && !state.compare.includes(id) && state.compare.length < 4) state.compare.push(id);
    renderCompare();
  });

  const links = [...document.querySelectorAll('.tabs a')];
  const spy = new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting) links.forEach((a) => a.classList.toggle('on', a.getAttribute('href') === '#' + e.target.id));
    }
  }, { rootMargin: '-45% 0px -50% 0px' });
  document.querySelectorAll('main section').forEach((s) => spy.observe(s));

  const fail = (err) => {
    const box = $('#error');
    box.hidden = false;
    box.textContent = t('load_fail');
    document.documentElement.dataset.error = String(err?.message || err);
  };
  addEventListener('error', (ev) => fail(ev.error || ev.message));
  addEventListener('unhandledrejection', (ev) => fail(ev.reason));

  fetch('data/app.json')
    .then((r) => { if (!r.ok) throw new Error('app.json ' + r.status); return r.json(); })
    .then((app) => {
      state.app = app;
      renderAll();
      document.documentElement.dataset.ready = '1';
      if (params.get('item')) openDetail(params.get('item'));
    })
    .catch(fail);
})();
