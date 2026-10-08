// Original DialysisLab geometric 5x7 glyphs, MIT. No imported font assets.
#include <lvgl/lvgl.h>
#include <array>
#include <cstring>
namespace {
struct Glyph { char ch; const char* rows; };
// Rows are five-bit hexadecimal masks; seven rows per character, top to bottom.
constexpr Glyph shapes[]={
 {'A',"0e11111f111111"},{'B',"1e11111e11111e"},{'C',"0f10101010100f"},
 {'D',"1e11111111111e"},{'E',"1f10101e10101f"},{'F',"1f10101e101010"},
 {'G',"0f10101711110f"},{'H',"1111111f111111"},{'I',"1f04040404041f"},
 {'J',"0702020212120c"},{'K',"11121418141211"},{'L',"1010101010101f"},
 {'M',"111b1511111111"},{'N',"11191513111111"},{'O',"0e11111111110e"},
 {'P',"1e11111e101010"},{'Q',"0e11111115120d"},{'R',"1e11111e141211"},
 {'S',"0f10100e01011e"},{'T',"1f040404040404"},{'U',"1111111111110e"},
 {'V',"11111111110a04"},{'W',"11111111151b11"},{'X',"11110a040a1111"},
 {'Y',"11110a04040404"},{'Z',"1f01020408101f"},
 {'a',"00000e010f110f"},{'b',"10101e1111111e"},{'c',"00000e1110100f"},
 {'d',"01010f1111110f"},{'e',"00000e111f100f"},{'f',"0609091c080808"},
 {'g',"000f11110f010e"},{'h',"10101e11111111"},{'i',"04000c0404040e"},
 {'j',"0200060202120c"},{'k',"101011121c1211"},{'l',"0c04040404040e"},
 {'m',"00001a15151515"},{'n',"00001e11111111"},{'o',"00000e1111110e"},
 {'p',"001e11111e1010"},{'q',"000f11110f0101"},{'r',"00001619101010"},
 {'s',"00000f100e011e"},{'t',"08081c08080906"},{'u',"0000111111130d"},
 {'v',"00001111110a04"},{'w',"0000111115150a"},{'x',"0000110a040a11"},
 {'y',"001111110f010e"},{'z',"00001f0204081f"},
 {'0',"0e11131519110e"},{'1',"040c040404040e"},{'2',"0e11010204081f"},
 {'3',"1e01010e01011e"},{'4',"02060a121f0202"},{'5',"1f10101e01011e"},
 {'6',"0710101e11110e"},{'7',"1f010204080808"},{'8',"0e11110e11110e"},
 {'9',"0e11110f01011c"},{' ',"00000000000000"},{'.',"00000000000c0c"},
 {',',"00000000000408"},{':',"000c0c000c0c00"},{';',"000c0c00000408"},
 {'-',"0000001f000000"},{'_',"0000000000001f"},{'/',"01020204080810"},
 {'\\',"10080804020201"},{'!',"04040404040004"},{'?',"0e110102040004"},
 {'(',"02040808080402"},{')',"08040202020408"},{'[',"0e08080808080e"},
 {']',"0e02020202020e"},{'+',"0004041f040400"},{'=',"00001f001f0000"},
 {'<',"01020408040201"},{'>',"10080402040810"},{'%',"191a0204080b13"},
 {'*',"00150e1f0e1500"},{'|',"04040404040404"},{'"',"0a0a0000000000"},
 {'\'',"04040000000000"},{'#',"0a0a1f0a1f0a0a"},{'@',"0e11171716100f"}
};
const std::array<std::array<unsigned char,140>,128>& pixels() {
    static const auto data=[] {
        std::array<std::array<unsigned char,140>,128> a{};
        auto hex=[](char c){return c<='9'?c-'0':c-'a'+10;};
        for (auto g:shapes) for(int y=0;y<7;++y) {
            auto bits=hex(g.rows[y*2])*16+hex(g.rows[y*2+1]);
            for(int x=0;x<5;++x) if(bits&(1<<(4-x)))
                for(int dy=0;dy<2;++dy) for(int dx=0;dx<2;++dx) a[static_cast<unsigned>(g.ch)][(y*2+dy)*10+x*2+dx]=255;
        }
        return a;
    }(); return data;
}
bool glyph(const lv_font_t* f,lv_font_glyph_dsc_t* d,uint32_t ch,uint32_t) {
    if(ch<32 || ch>=127) ch='?';
    d->resolved_font=f; d->gid.index=ch; d->adv_w=12; d->box_w=ch==' '?0:10; d->box_h=ch==' '?0:14;
    d->ofs_x=0; d->ofs_y=0; d->stride=10; d->format=LV_FONT_GLYPH_FORMAT_A8; return true;
}
const void* bitmap(lv_font_glyph_dsc_t* d,lv_draw_buf_t* b) {
    auto& p=pixels()[d->gid.index];
    if(d->req_raw_bitmap) return p.data();
    if(!b) return nullptr;
    for(unsigned y=0;y<14;++y) std::memcpy(b->data+y*b->header.stride,p.data()+10*y,10);
    return b;
}
}
const lv_font_t dialysis_font=[] {
    lv_font_t f{}; f.get_glyph_dsc=glyph; f.get_glyph_bitmap=bitmap;
    f.line_height=19; f.cap_height=14; f.x_height=10; f.static_bitmap=1; return f;
}();
