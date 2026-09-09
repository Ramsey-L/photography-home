(function () {
  'use strict';

  var viewport = document.getElementById('map-viewport');
  var world = document.getElementById('photo-world');
  var player = document.getElementById('player');
  var landmarksRoot = document.getElementById('landmarks');
  var collectiblesRoot = document.getElementById('collectibles');
  var nearbyIndex = document.getElementById('nearby-index');
  var nearbyTitle = document.getElementById('nearby-title');
  var nearbyMeta = document.getElementById('nearby-meta');
  var openAlbum = document.getElementById('open-album');
  var filmCount = document.getElementById('film-count');
  var soundToggle = document.getElementById('sound-toggle');
  var activeMoves = new Set();
  var albums = [];
  var landmarks = [];
  var films = [];
  var nearest = null;
  var lastFrame = performance.now();
  var playerPosition = { x: 240, y: 560 };
  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var storageKey = 'zncu-photo-films';
  var collected = new Set(JSON.parse(localStorage.getItem(storageKey) || '[]'));

  var positions = [
    [.12, .22], [.27, .13], [.43, .24], [.60, .14], [.79, .22],
    [.91, .40], [.74, .43], [.56, .38], [.39, .47], [.20, .43],
    [.10, .69], [.29, .72], [.48, .66], [.68, .74], [.86, .67]
  ];

  var filmPositions = [
    [.18, .33], [.49, .14], [.83, .32], [.31, .59], [.62, .57], [.78, .84]
  ];

  function worldSize() {
    return { width: world.offsetWidth, height: world.offsetHeight };
  }

  function setPlayerPosition(x, y) {
    var size = worldSize();
    playerPosition.x = Math.max(55, Math.min(size.width - 55, x));
    playerPosition.y = Math.max(120, Math.min(size.height - 45, y));
    player.style.left = playerPosition.x + 'px';
    player.style.top = playerPosition.y + 'px';
  }

  function positionCamera() {
    var size = worldSize();
    var minX = Math.min(0, viewport.clientWidth - size.width);
    var minY = Math.min(0, viewport.clientHeight - size.height);
    var x = Math.max(minX, Math.min(0, viewport.clientWidth / 2 - playerPosition.x));
    var y = Math.max(minY, Math.min(0, viewport.clientHeight / 2 - playerPosition.y));
    world.style.transform = 'translate3d(' + x + 'px,' + y + 'px,0)';
  }

  function layoutObjects() {
    var size = worldSize();
    landmarks.forEach(function (item, index) {
      item.x = positions[index % positions.length][0] * size.width;
      item.y = positions[index % positions.length][1] * size.height;
      item.element.style.left = item.x + 'px';
      item.element.style.top = item.y + 'px';
    });
    films.forEach(function (item, index) {
      item.x = filmPositions[index][0] * size.width;
      item.y = filmPositions[index][1] * size.height;
      item.element.style.left = item.x + 'px';
      item.element.style.top = item.y + 'px';
    });
    setPlayerPosition(playerPosition.x, playerPosition.y);
    positionCamera();
  }

  function makeLandmarks(data) {
    landmarksRoot.textContent = '';
    landmarks = data.map(function (album, index) {
      var link = document.createElement('a');
      link.className = 'landmark';
      link.href = album.route;
      link.style.setProperty('--tilt', ((index % 5) - 2) * 1.6 + 'deg');
      link.setAttribute('aria-label', album.title + '，' + album.photos + ' 张照片');
      link.innerHTML =
        '<img src="' + album.cover + '" alt="" width="320" height="220" loading="lazy">' +
        '<span class="landmark-label"><strong>' + escapeHtml(album.title) + '</strong><span>' +
        escapeHtml(album.date.replaceAll('.', '/')) + '</span></span>';
      landmarksRoot.appendChild(link);
      return { album: album, element: link, x: 0, y: 0 };
    });
  }

  function makeFilms() {
    collectiblesRoot.textContent = '';
    films = filmPositions.map(function (_, index) {
      var element = document.createElement('span');
      element.className = 'film' + (collected.has(index) ? ' is-collected' : '');
      element.setAttribute('aria-hidden', 'true');
      collectiblesRoot.appendChild(element);
      return { id: index, element: element, x: 0, y: 0 };
    });
    updateFilmCount();
  }

  function escapeHtml(value) {
    var span = document.createElement('span');
    span.textContent = value;
    return span.innerHTML;
  }

  function distance(a, b) {
    return Math.hypot(a.x - b.x, a.y - b.y);
  }

  function updateNearby() {
    var candidate = null;
    var candidateDistance = Infinity;
    landmarks.forEach(function (item) {
      var d = distance(playerPosition, item);
      item.element.classList.toggle('is-near', d < 145);
      if (d < candidateDistance) {
        candidate = item;
        candidateDistance = d;
      }
    });

    if (candidate && candidateDistance < 145) {
      if (nearest !== candidate) playTone(520, .05);
      nearest = candidate;
      nearbyIndex.textContent = '发现相册';
      nearbyTitle.textContent = candidate.album.title;
      nearbyMeta.textContent = candidate.album.date + ' · ' + candidate.album.photos + ' 张照片';
      openAlbum.href = candidate.album.route;
      openAlbum.hidden = false;
    } else {
      nearest = null;
      nearbyIndex.textContent = '探索中';
      nearbyTitle.textContent = '沿着地图走走';
      nearbyMeta.textContent = '相册会在靠近时回应你';
      openAlbum.hidden = true;
    }

    films.forEach(function (film) {
      if (!collected.has(film.id) && distance(playerPosition, film) < 54) {
        collected.add(film.id);
        film.element.classList.add('is-collected');
        localStorage.setItem(storageKey, JSON.stringify(Array.from(collected)));
        updateFilmCount();
        playTone(780, .12);
      }
    });
  }

  function updateFilmCount() {
    filmCount.textContent = Math.min(collected.size, filmPositions.length);
    if (collected.size >= filmPositions.length) {
      nearbyIndex.textContent = '暗房收藏完成';
    }
  }

  function playTone(frequency, duration) {
    if (!soundToggle.checked) return;
    var AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;
    var context = new AudioContext();
    var oscillator = context.createOscillator();
    var gain = context.createGain();
    oscillator.type = 'sine';
    oscillator.frequency.value = frequency;
    gain.gain.setValueAtTime(.05, context.currentTime);
    gain.gain.exponentialRampToValueAtTime(.001, context.currentTime + duration);
    oscillator.connect(gain);
    gain.connect(context.destination);
    oscillator.start();
    oscillator.stop(context.currentTime + duration);
  }

  function frame(now) {
    var delta = Math.min(.035, (now - lastFrame) / 1000);
    lastFrame = now;
    var dx = 0;
    var dy = 0;
    if (activeMoves.has('left')) dx -= 1;
    if (activeMoves.has('right')) dx += 1;
    if (activeMoves.has('up')) dy -= 1;
    if (activeMoves.has('down')) dy += 1;

    if (dx || dy) {
      var length = Math.hypot(dx, dy);
      var speed = reducedMotion ? 330 : 260;
      setPlayerPosition(
        playerPosition.x + dx / length * speed * delta,
        playerPosition.y + dy / length * speed * delta
      );
      player.classList.add('is-moving');
      player.classList.toggle('is-left', dx < 0);
      positionCamera();
      updateNearby();
    } else {
      player.classList.remove('is-moving');
    }
    requestAnimationFrame(frame);
  }

  function bindControls() {
    var keyMap = {
      ArrowUp: 'up', w: 'up', W: 'up',
      ArrowDown: 'down', s: 'down', S: 'down',
      ArrowLeft: 'left', a: 'left', A: 'left',
      ArrowRight: 'right', d: 'right', D: 'right'
    };

    window.addEventListener('keydown', function (event) {
      var move = keyMap[event.key];
      if (move) {
        event.preventDefault();
        activeMoves.add(move);
      }
      if ((event.key === 'Enter' || event.key === 'e' || event.key === 'E') && nearest) {
        window.location.href = nearest.album.route;
      }
    });

    window.addEventListener('keyup', function (event) {
      var move = keyMap[event.key];
      if (move) activeMoves.delete(move);
    });

    document.querySelectorAll('[data-move]').forEach(function (button) {
      var move = button.dataset.move;
      function start(event) {
        event.preventDefault();
        activeMoves.add(move);
        button.classList.add('is-active');
      }
      function stop() {
        activeMoves.delete(move);
        button.classList.remove('is-active');
      }
      button.addEventListener('pointerdown', start);
      button.addEventListener('pointerup', stop);
      button.addEventListener('pointercancel', stop);
      button.addEventListener('pointerleave', stop);
    });

    window.addEventListener('blur', function () {
      activeMoves.clear();
      document.querySelectorAll('.move-pad .is-active').forEach(function (button) {
        button.classList.remove('is-active');
      });
    });
    window.addEventListener('resize', layoutObjects);
  }

  function trackVisit() {
    if (/^(localhost|127\.0\.0\.1)$/.test(window.location.hostname)) return;
    var key = 'zncu-photo-visitor';
    var visitorId = localStorage.getItem(key);
    if (!visitorId) {
      visitorId = window.crypto && crypto.randomUUID ? crypto.randomUUID() :
        'v-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2);
      localStorage.setItem(key, visitorId);
    }
    fetch('/api/visit', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ visitorId: visitorId, path: '/explore/' }),
      keepalive: true
    }).catch(function () {});
  }

  Promise.all([
    fetch('/explore/albums.json', { cache: 'no-store' }).then(function (response) {
      if (!response.ok) throw new Error('album data unavailable');
      return response.json();
    })
  ]).then(function (result) {
    albums = result[0];
    makeLandmarks(albums);
    makeFilms();
    var size = worldSize();
    playerPosition = { x: size.width * .14, y: size.height * .54 };
    layoutObjects();
    updateNearby();
    bindControls();
    requestAnimationFrame(frame);
  }).catch(function () {
    nearbyTitle.textContent = '地图暂时没有显影';
    nearbyMeta.textContent = '返回摄影日志继续浏览';
  });

  trackVisit();
})();
