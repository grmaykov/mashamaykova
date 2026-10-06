/* Rebuild static search-friendly pages after editing app.js or data.js: node .seo/build.cjs */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),read=p=>fs.readFileSync(path.join(root,p),'utf8');
const app=read('app.js'),data=read('data.js');
const ctx=vm.createContext({URLSearchParams,location:{pathname:'/',search:'',hash:''},Map});
vm.runInContext(data+'\n'+app.slice(0,app.indexOf("$('#main').addEventListener")),ctx);
const routes=['paintings','graphic-art','about','contact'];
const base='https://mashamaykova.com';
let template=read('.seo/template.html').replace('<head>','<head><base href="/">')
 .replace(/<button data-lang="(en|ru)" aria-label="([^"]+)">(EN|RU)<\/button>/g,'<a data-lang="$1" aria-label="$2">$3</a>')
 .replace(/style.css\?v=[^"]+/g,'style.css?v=seo-1').replace(/data.js\?v=[^"]+/g,'data.js?v=seo-1').replace(/app.js\?v=[^"]+/g,'app.js?v=seo-2');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const urls=[];
for(const language of ['en','ru'])for(const route of routes){
 const result=vm.runInContext(`lang=${JSON.stringify(language)};route=${JSON.stringify(route)};shown=ARTWORKS.length;({url:pagePath(),title:tr[lang].name+' — '+tr[lang].nav[routes.indexOf(route)],description:SEO_DESCRIPTIONS[lang][route],name:tr[lang].name,menu:tr[lang].menu,back:tr[lang].back,rights:tr[lang].rights,nav:routes.map((r,j)=>'<a href="'+pagePath(r)+'" '+(r===route?'aria-current="page"':'')+'>'+tr[lang].nav[j]+'</a>').join(''),body:heading(routes.indexOf(route))+(route==='paintings'||route==='graphic-art'?gallery():route==='about'?about():contact()),alternates:['en','ru','x-default'].map(l=>({lang:l,url:pagePath(route,l==='ru'?'ru':'en')})),images:ARTWORKS.filter(w=>w.category===route).map(w=>artworkImage(w))})`,ctx);
 const url=base+result.url;urls.push({url,alternates:result.alternates,images:result.images});
 const metadata=`<link rel="canonical" href="${url}">`+result.alternates.map(a=>`<link rel="alternate" hreflang="${a.lang}" href="${base+a.url}">`).join('')+`<meta property="og:type" content="website"><meta property="og:site_name" content="Masha Maykova"><meta property="og:title" content="${esc(result.title)}"><meta property="og:description" content="${esc(result.description)}"><meta property="og:url" content="${url}"><meta property="og:locale" content="${language==='ru'?'ru_RU':'en_US'}"><meta property="og:image" content="${base}/assets/0669.webp"><meta name="twitter:card" content="summary_large_image"><script type="application/ld+json">${JSON.stringify({'@context':'https://schema.org','@graph':[{'@type':'WebSite','@id':base+'/#website',url:base+'/',name:'Masha Maykova — Маша Майкова',inLanguage:['en','ru']},{'@type':'Person','@id':base+'/#artist',name:'Маша Майкова',alternateName:'Masha Maykova',url:base+'/',jobTitle:language==='ru'?'Художник':'Artist',knowsAbout:language==='ru'?['Живопись','Графика','Дизайн интерьеров','Декорирование интерьеров']:['Painting','Graphic art','Interior design','Interior decoration']},{'@type':'WebPage',url,name:result.title,description:result.description,inLanguage:language,about:{'@id':base+'/#artist'},isPartOf:{'@id':base+'/#website'}}]})}</script>`;
 let html=template.replace('<html lang="en">',`<html lang="${language}">`).replace(/<title>.*?<\/title>/,`<title>${esc(result.title)}</title>`).replace(/<meta name="description" content="[^"]*">/,`<meta name="description" content="${esc(result.description)}">`).replace('</head>',metadata+'</head>')
 .replace('<body>',`<body data-page="${route}">`).replace('<nav aria-label="Main navigation"></nav>',`<nav aria-label="Main navigation">${result.nav}</nav>`)
 .replace('<main id="main" tabindex="-1"></main>',`<main id="main" tabindex="-1">${result.body}</main>`)
 .replace(/<a class="signature"[^>]*>.*?<\/a>/,`<a class="signature" href="${language==='ru'?'/ru/':'/'}" aria-label="${esc(result.name)}">${result.name}</a>`)
 .replace('<span class="footer-name">Masha Maykova</span>',`<span class="footer-name">${result.name}</span>`)
 .replace('<span id="copyright"></span>',`<span id="copyright">© ${new Date().getFullYear()} ${result.name}. ${result.rights}.</span>`)
 .replace(/<a href="#paintings" id="back-top">.*?<\/a>/,`<a href="${language==='ru'?'/ru/':'/'}" id="back-top">${result.back}</a>`)
 .replace('href="#main"',`href="${result.url}#main"`)
 .replace(/<a data-lang="(en|ru)" aria-label="([^"]+)">/g,(_,l,label)=>`<a data-lang="${l}" href="${result.alternates.find(a=>a.lang===l).url}" aria-label="${label}"${l===language?' class="active" aria-current="true"':''}>`);
 const dest=path.join(root,result.url,'index.html');fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,html);
}
const xml='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'+urls.map(r=>'<url><loc>'+r.url+'</loc>'+r.alternates.map(a=>`<xhtml:link rel="alternate" hreflang="${a.lang}" href="${base+a.url}"/>`).join('')+r.images.map(src=>`<image:image><image:loc>${base+'/'+src}</image:loc></image:image>`).join('')+'</url>').join('\n')+'\n</urlset>\n';
fs.writeFileSync(path.join(root,'sitemap.xml'),xml);
fs.writeFileSync(path.join(root,'robots.txt'),'User-agent: *\nAllow: /\n\nSitemap: '+base+'/sitemap.xml\n');
console.log('Built '+urls.length+' static pages and image sitemap.');
