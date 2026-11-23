import sys, asyncio, pathlib
from playwright.async_api import async_playwright
ROOT=pathlib.Path(__file__).resolve().parent.parent
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome')
        for w in (1200,400):
            pg=await b.new_page(viewport={'width':w,'height':900})
            errs=[]
            pg.on('console',lambda m: errs.append(m.text) if m.type in ('error','warning') else None)
            pg.on('pageerror',lambda e: errs.append('PAGEERROR '+str(e)))
            await pg.goto((ROOT/'dist'/'preview.html').as_uri()); await pg.wait_for_timeout(800)
            for t in ['overview','sana','kitchen','staffing','strategy']:
                await pg.click(f'.tab[data-tab="{t}"]'); await pg.wait_for_timeout(400)
                if t=='strategy': await pg.evaluate("document.getElementById('assume').open=true"); await pg.wait_for_timeout(300)
                await pg.screenshot(path=str(ROOT/'dist'/f'shot_{w}_{t}.png'),full_page=True)
            print(w,'errors:',errs[:10])
            txt=await pg.evaluate("document.querySelector('#takeaway').textContent+' || '+document.querySelector('#stratRead').textContent")
            print(txt)
        await b.close()
asyncio.run(main())
