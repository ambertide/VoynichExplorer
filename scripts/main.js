function changeVoynichFont(value) {
    var voynichTextRule = document.styleSheets[2].rules[1].style;
    switch (value) {
        case "1":
            voynichTextRule.fontFamily = 'Roboto';
            voynichTextRule.fontWeight = 'normal';
            break;
        case "0":
            voynichTextRule.fontFamily = 'EVA';
            voynichTextRule.fontWeight = 'bold';
            break;
    }
}