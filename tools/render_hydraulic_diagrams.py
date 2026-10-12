#!/usr/bin/env python3
"""Generate original, static SVG hydraulic illustrations (standard library only)."""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'docs/diagrams'
INK, BLOOD, WATER, SUB, GRAY = '#203246', '#ad3248', '#19718b', '#7960a6', '#637589'


class Drawing:
    def __init__(self, title, subtitle, height=760):
        self.height = height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="{height}" viewBox="0 0 1200 {height}" role="img">',
                      f'<title>{escape(title)}</title>', f'<desc>{escape(subtitle)}</desc>',
                      '<rect width="1200" height="100%" fill="#ffffff"/>']
        self.text(40, 45, title, 28, bold=True)
        self.text(40, 75, subtitle, 16, GRAY)
        self.line(40, 96, 1160, 96, '#d6dfe7', width=1)

    def text(self, x, y, value, size=17, color=INK, bold=False, anchor='start'):
        self.parts.append(f'<text x="{x}" y="{y}" font-family="DejaVu Sans, sans-serif" font-size="{size}" fill="{color}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{escape(value)}</text>')

    def path(self, d, color=INK, width=3, dash=False, fill='none'):
        self.parts.append(f'<path d="{d}" stroke="{color}" stroke-width="{width}" fill="{fill}" stroke-linejoin="round" stroke-linecap="round"'+(' stroke-dasharray="8 6"' if dash else '')+'/>')

    def line(self, x1, y1, x2, y2, color=INK, width=3, dash=False):
        self.path(f'M{x1},{y1} L{x2},{y2}', color, width, dash)

    def circle(self, x, y, r, color=INK, fill='white', width=3):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{r}" stroke="{color}" stroke-width="{width}" fill="{fill}"/>')

    def rect(self, x, y, w, h, color=INK, fill='white', dash=False):
        self.path(f'M{x},{y} h{w} v{h} h-{w} Z', color, 2, dash, fill)

    def arrow(self, x, y, direction='right', color=INK):
        paths = {'right': f'M{x-10},{y-5} L{x},{y} L{x-10},{y+5}',
                 'left': f'M{x+10},{y-5} L{x},{y} L{x+10},{y+5}',
                 'down': f'M{x-5},{y-10} L{x},{y} L{x+5},{y-10}',
                 'up': f'M{x-5},{y+10} L{x},{y} L{x+5},{y+10}'}
        self.path(paths[direction], color, 2)

    def pump(self, x, y, color=BLOOD, direction='right', r=27):
        self.circle(x,y,r,color)
        if direction=='right': self.path(f'M{x-9},{y-12} L{x+15},{y} L{x-9},{y+12} Z',color,2,fill=color)
        else: self.path(f'M{x-12},{y-9} L{x},{y+15} L{x+12},{y-9} Z',color,2,fill=color)

    def resistor(self,x,y,w=110,color=BLOOD,label='R'):
        self.rect(x,y-13,w,26,color)
        self.text(x+w/2,y-27,label,17,color,anchor='middle')

    def gauge(self,x,y,label):
        self.circle(x,y,21)
        self.line(x,y,x+10,y-10,width=2)
        self.text(x,y-34,label,17,anchor='middle')

    def reservoir(self,x,y,w=100,h=70,color=INK):
        self.path(f'M{x},{y} v{h} h{w} v-{h}',color)
        self.line(x+5,y+24,x+w-5,y+24,color,width=2)
        self.line(x+14,y+34,x+w-14,y+34,color,width=1)

    def note(self, y, title, lines):
        self.rect(40,y,1120,38+len(lines)*25,'#d6dfe7','#f4f7fa')
        self.text(58,y+27,title,17,bold=True)
        for i,t in enumerate(lines): self.text(58,y+53+i*25,t,16)

    def save(self,name):
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/name).write_text('\n'.join(self.parts+['</svg>'])+'\n')


def extracorporeal():
    d=Drawing('Extracorporeal circuit — treatment reference',
              'Functional hydraulic schematic: physical route, not the default solver topology.')
    d.reservoir(70,275,125,130,BLOOD)
    d.text(70,235,'Patient connection',19,bold=True)
    d.text(70,258,'Common supply / return',15,GRAY)
    d.path('M105,405 V455 H1060 V300 H960',BLOOD)
    d.path('M160,300 H320',BLOOD)
    d.pump(347,300)
    d.path('M374,300 H670',BLOOD)
    d.text(347,358,'Blood pump',17,anchor='middle')
    d.arrow(265,300,color=BLOOD); d.arrow(600,300,color=BLOOD)
    d.line(500,300,500,237,BLOOD);d.gauge(500,216,'P blood')
    d.circle(500,300,4,BLOOD,BLOOD)
    # Four-port membrane cartridge: longitudinal blood and dialysate passages.
    d.rect(670,260,290,110,INK,'#fafbfc')
    d.line(670,300,960,300,BLOOD)
    d.line(670,345,960,345,WATER)
    d.line(685,323,945,323,GRAY,width=2,dash=True)
    d.path('M670,345 H630 V410',WATER)
    d.path('M960,345 H1015 V400',WATER)
    d.arrow(725,300,color=BLOOD);d.arrow(850,345,'left',WATER)
    d.text(815,225,'Dialyzer',21,bold=True,anchor='middle')
    d.text(815,246,'Two fluid passages / one membrane',14,GRAY,anchor='middle')
    d.text(630,434,'Spent dialysate',14,WATER,anchor='middle')
    d.text(1015,425,'Fresh dialysate',14,WATER,anchor='middle')
    d.arrow(630,405,'down',WATER);d.arrow(1015,370,'up',WATER)
    d.arrow(880,455,'left',BLOOD);d.text(580,481,'Venous return',17,BLOOD)
    d.text(205,326,'Withdrawal',14,BLOOD)
    # Alternative injection routes are dashed to avoid simultaneous-route implication.
    d.path('M550,145 H570 V300',SUB,dash=True)
    d.path('M850,145 H1095 V455 H1060',SUB,dash=True)
    d.circle(570,300,5,SUB,SUB);d.circle(1060,455,5,SUB,SUB)
    d.arrow(570,280,'down',SUB);d.arrow(1095,430,'down',SUB)
    d.text(550,128,'Pre-HDF inlet',16,SUB)
    d.text(850,128,'Post-HDF inlet',16,SUB)
    d.text(42,535,'LEGEND',15,bold=True)
    d.line(145,530,185,530,BLOOD);d.text(198,535,'Blood',16)
    d.line(305,530,345,530,WATER);d.text(358,535,'Dialysate',16)
    d.line(520,530,560,530,SUB,dash=True);d.text(573,535,'Alternative substitution route',16)
    d.note(568,'How to read this drawing',[
        'Select pre- OR postdilution for HDF; neither inlet supplies substitution in HD.',
        'The default solver collapses the blood path to one pressure node and one dialyzer resistance.',
        'Tubing sections and the dialysate counterflow route are illustrative, not spatially resolved.',
        'No separate air trap, bubble transport or arterial/venous pressure network is implemented.'
    ])
    d.save('extracorporeal-reference.svg')


def equivalent():
    d=Drawing('Blood circuit — implemented hydraulic equivalent',
              'Exact default graph in scenarios/machine_hdf_pre.json; lumped hydraulic quantities.',820)
    d.reservoir(65,245,110,90,BLOOD)
    d.text(55,196,'Node 0',20,bold=True);d.text(55,221,'P₀ = 0 mmHg',17)
    d.path('M175,290 H262',BLOOD);d.pump(290,290,r=28)
    d.path('M318,290 H620',BLOOD)
    d.circle(620,290,6,BLOOD,BLOOD)
    d.line(620,290,800,290,BLOOD)
    d.resistor(800,290,120,label='R dialyzer')
    d.path('M920,290 H1080 V510 H120 V335',BLOOD)
    d.arrow(490,290,color=BLOOD);d.arrow(1025,290,color=BLOOD)
    d.arrow(950,510,'left',BLOOD)
    d.text(290,355,'Finite-head pump',18,anchor='middle')
    d.text(290,379,'Demand D; head H',16,GRAY,anchor='middle')
    d.line(620,290,620,210,BLOOD);d.gauge(620,189,'Node 1: P₁')
    d.text(830,346,'Qedge = (P₁ − P₀) / R',17,BLOOD)
    # Shunt compliance is storage, not a return line through the capacitor.
    d.line(620,290,620,388,BLOOD)
    d.line(590,388,650,388,BLOOD);d.line(590,405,650,405,BLOOD)
    d.line(620,405,620,458,GRAY)
    d.line(600,458,640,458,GRAY);d.line(605,466,635,466,GRAY);d.line(613,474,627,474,GRAY)
    d.text(578,401,'C₁ compliance',17,anchor='end')
    d.text(578,426,'Stored volume = C₁P₁',15,GRAY,anchor='end')
    # Withdrawal current source analog.
    d.path('M745,290 V555',BLOOD);d.circle(745,290,4,BLOOD,BLOOD)
    d.pump(745,582,WATER,'down')
    d.line(745,609,745,636,WATER);d.arrow(745,635,'down',WATER)
    d.text(785,574,'Quf: limited water removal',17,WATER)
    d.text(785,599,'Sink to removed-fluid ledger',15,GRAY)
    # break crossing of return and UF visually with bridge? separate route UF outside return avoid crossing ambiguity
    d.circle(745,510,15,'white','white',1);d.path('M745,495 Q765,510 745,525',BLOOD)
    d.text(65,555,'Lower line returns to the same node 0.',15,GRAY)
    d.text(65,580,'A crossing without a dot is not a junction.',15,GRAY)
    # Predilution enters via separate pressure-limited source.
    d.path('M420,139 V190',SUB);d.pump(420,217,SUB,'down')
    d.line(420,244,420,290,SUB);d.circle(420,290,4,SUB,SUB)
    d.text(265,126,'Pre-HDF: delivered substitution Qsub',17,SUB)
    d.note(667,'Model boundaries',[
        'C₁ = 0.001 mL/mmHg and R = 1 mmHg·min/mL in this example; parameters are synthetic.',
        'The compliance reference is P₀; the plates denote elastic storage, not a valve or flowing branch.',
        'Post-HDF substitution goes to the patient extracellular pool, not to node 1. Dialysate pressure = 0.'
    ])
    d.save('hydraulic-equivalent.svg')


def preparation():
    d=Drawing('Dialysate and substitution — preparation model',
              'Open tank, heater, filters and pump symbols; no complete dialysate pressure-network solver.',820)
    d.path('M70,200 H350 V255',WATER);d.arrow(260,200,color=WATER)
    d.text(65,170,'Water supply',19,WATER,bold=True)
    d.path('M290,135 H445 V255',SUB);d.arrow(445,240,'down',SUB)
    d.text(290,121,'Concentrate ratio',17,SUB)
    d.reservoir(295,255,250,180,WATER)
    d.text(320,315,'Mixed reservoir',20,bold=True)
    d.text(320,342,'Volume V',16);d.text(320,366,'Composition / T',16)
    d.path('M335,402 h25 l10,-12 l20,24 l20,-24 l20,24 l10,-12 h25',INK,width=2)
    d.text(375,478,'Heater',17,anchor='middle')
    d.line(430,435,430,455,INK);d.line(395,455,465,455,INK,width=2)
    d.path('M545,325 H820',WATER);d.arrow(790,325,color=WATER)
    d.text(640,285,'Qd and Cd',18,WATER)
    # Compact membrane hydraulic element with external drain boundary.
    d.rect(820,290,125,95,INK,'#fafbfc')
    d.line(832,336,933,336,GRAY,dash=True)
    d.line(820,325,945,325,WATER)
    d.path('M945,325 H1090 V395',WATER);d.arrow(1090,382,'down',WATER)
    d.path('M1065,402 h50 M1073,411 h34 M1082,420 h16',GRAY,width=2)
    d.text(815,263,'Dialyzer boundary',17,bold=True)
    d.text(1010,455,'Spent fluid',16,WATER)
    # filtered substitution branch
    d.path('M545,405 H600 V565 H680',SUB)
    for x,label in [(680,'Filter 1'),(830,'Filter 2')]:
        d.path(f'M{x},565 l35,-35 l35,35 l-35,35 Z',SUB,2,fill='white')
        d.line(x+18,582,x+52,548,SUB,width=2,dash=True)
        d.text(x+35,626,label,17,SUB,anchor='middle')
    d.line(750,565,830,565,SUB)
    d.line(900,565,967,565,SUB);d.pump(994,565,SUB)
    d.path('M1021,565 H1110 V650',SUB);d.arrow(1110,638,'down',SUB)
    d.text(965,520,'Delivery pump',17,SUB)
    d.text(790,675,'To selected pre- or postdilution inlet',17,SUB)
    d.note(709,'Represented effects',[
        'Tank mixing and temperature; ionic conductivity estimate; filter/line pressure losses; finite pump head.',
        'Filter penetration acts on a synthetic contamination indicator. This does not model sterility.'
    ])
    d.save('fluid-preparation.svg')


def dialyzer():
    d=Drawing('Dialyzer — membrane transport model',
              'Cross-section illustration; the implementation uses mixed pools, not resolved hollow-fibre geometry.',700)
    d.rect(225,205,750,300,INK,'#fafbfc')
    d.rect(226,206,748,136,'#faedef','#faedef')
    d.rect(226,369,748,135,'#eaf5f8','#eaf5f8')
    d.line(225,345,975,345,GRAY,width=3);d.line(225,366,975,366,GRAY,width=3)
    d.path('M65,265 H225 M975,265 H1135',BLOOD)
    d.path('M1135,438 H975 M225,438 H65',WATER)
    d.arrow(175,265,color=BLOOD);d.arrow(1100,265,color=BLOOD)
    d.arrow(1030,438,'left',WATER);d.arrow(105,438,'left',WATER)
    d.text(245,185,'Blood side: one mixed extracorporeal pool',19,BLOOD,bold=True)
    d.text(245,535,'Dialysate side: specified flow Qd and composition Cd',19,WATER,bold=True)
    d.text(65,239,'Qb, Cb',17,BLOOD);d.text(1010,239,'Blood return',16,BLOOD)
    d.text(1005,473,'Fresh fluid',16,WATER);d.text(60,473,'Spent fluid',16,WATER)
    d.line(415,305,415,405,SUB,width=3);d.arrow(415,305,'up',SUB);d.arrow(415,405,'down',SUB)
    d.text(415,285,'Diffusion',18,SUB,True,anchor='middle')
    d.text(415,462,'K × (Cb − Cd)',17,SUB,anchor='middle')
    d.line(755,305,755,405,WATER,width=5);d.arrow(755,405,'down',WATER)
    d.text(755,285,'Water + convection',18,WATER,True,anchor='middle')
    d.text(755,462,'Quf × sieving × Cb',17,WATER,anchor='middle')
    d.text(580,361,'Membrane',14,GRAY,anchor='middle')
    d.note(574,'Reading the symbols',[
        'Opposed ports illustrate the treatment route; there is no axial or countercurrent concentration solver.',
        'Diffusion can reverse with concentration gradient. Water removal is separately limited by pressure.',
        'Expressions show proportionality; implementation uses explicit mL-to-L conversions for solute flux.'
    ])
    d.save('dialyzer-transport.svg')


if __name__ == '__main__':
    extracorporeal()
    equivalent()
    preparation()
    dialyzer()
