const pptxgen = require('pptxgenjs');
const cheerio = require('cheerio');
const fs = require('fs');
const path = require('path');

async function createPptx() {
    const htmlPath = 'd:/anaconda/envs/agent/my_agent/temp_science_agent_slides.html';
    const outputPath = 'd:/anaconda/envs/agent/my_agent/科普智能体_演示文稿.pptx';

    const htmlContent = fs.readFileSync(htmlPath, 'utf8');
    const $ = cheerio.load(htmlContent);

    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';

    const slidesData = [];
    $('.slide').each((i, el) => {
        const $el = $(el);
        const h1 = $el.find('h1').text();
        const h2 = $el.find('h2').text();
        const subtitle = $el.find('.subtitle').text();
        // Get paragraph text excluding subtitle
        const p = $el.find('p').not('.subtitle').text();
        
        const bullets = [];
        $el.find('li').each((j, li) => {
            bullets.push($(li).text());
        });

        slidesData.push({
            title: h1 || h2 || '',
            subtitle: subtitle || '',
            body: p || '',
            bullets: bullets,
            isTitleSlide: !!h1
        });
    });

    for (const data of slidesData) {
        const slide = pptx.addSlide();
        slide.background = { color: '0F172A' };

        if (data.isTitleSlide) {
            slide.addText(data.title, {
                x: 0.5, y: 1.5, w: '90%', h: 1,
                fontSize: 44, color: '38BDF8', align: 'center', bold: true
            });
            slide.addText(data.subtitle, {
                x: 0.5, y: 2.5, w: '90%', h: 0.5,
                fontSize: 24, color: '94A3B8', align: 'center'
            });
        } else {
            slide.addText(data.title, {
                x: 0.5, y: 0.3, w: '90%', h: 0.8,
                fontSize: 32, color: '38BDF8', align: 'left', bold: true
            });
            
            slide.addShape(pptx.ShapeType.line, {
                x: 0.5, y: 1.1, w: 8, h: 0, line: { color: '38BDF8', width: 2 }
            });

            if (data.body) {
                slide.addText(data.body, {
                    x: 0.5, y: 1.3, w: '90%', h: 0.5,
                    fontSize: 20, color: 'F8FAFC'
                });
            }

            if (data.bullets && data.bullets.length > 0) {
                const bulletItems = data.bullets.map(text => { 
                    return { text: text, options: { bullet: true, color: 'F8FAFC', fontSize: 18 } } 
                });
                slide.addText(bulletItems, { x: 0.8, y: 1.8, w: '85%', h: 4 });
            }
        }
    }

    await pptx.writeFile({ fileName: outputPath });
    console.log('PPTX created at: ' + outputPath);
}

createPptx().catch(err => {
    console.error(err);
    process.exit(1);
});
