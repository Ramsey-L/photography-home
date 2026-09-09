const fs = require('node:fs');

hexo.extend.generator.register('cloudflare-routes', function () {
  return {
    path: '_routes.json',
    data: fs.readFileSync(hexo.source_dir + '_routes.json')
  };
});
