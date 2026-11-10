const fs = require('fs');
const path = require('path');

test('camera boundary editor scales clicks, undoes corners and exports normalized JSON', async () => {
  const html = fs.readFileSync(path.join(__dirname, '../../computer-vision/roi-editor.html'), 'utf8');
  const script = html.match(/<script>([\s\S]*?)<\/script>/)[1];
  document.body.innerHTML = html.match(/<body>([\s\S]*?)<script>/)[1];
  const context = Object.fromEntries(['clearRect','drawImage','beginPath','moveTo','lineTo','closePath','fill','stroke','arc','fillText'].map(name => [name, jest.fn()]));
  const canvas = document.getElementById('canvas');
  canvas.getContext = () => context;
  canvas.getBoundingClientRect = () => ({left:10,top:20,width:640,height:360});
  const originalImage = global.Image;
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  const click = jest.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  let exported;
  global.Image = class {
    constructor() { this.naturalWidth=1280; this.naturalHeight=720; }
    set src(value) { this.onload(); }
  };
  URL.createObjectURL = jest.fn(value => { if (!(value instanceof File)) exported=value; return 'blob:test'; });
  URL.revokeObjectURL = jest.fn();
  jest.useFakeTimers();
  try {
    // Execute the exact standalone editor script with browser DOM APIs.
    new Function(script)();
    const file = document.getElementById('file');
    Object.defineProperty(file, 'files', {value:[new File(['image'], 'live-frame.jpg')]});
    file.dispatchEvent(new Event('change'));
    const add = (x,y) => canvas.dispatchEvent(new MouseEvent('click', {clientX:x,clientY:y}));
    add(74,56); add(586,56); add(586,344);
    expect(document.getElementById('save').disabled).toBe(false);
    document.getElementById('undo').click();
    expect(document.getElementById('save').disabled).toBe(true);
    add(586,344);
    document.getElementById('save').click();
    expect(click).toHaveBeenCalledTimes(1);
    const reader = new FileReader();
    const result = new Promise(resolve => { reader.onload=()=>resolve(JSON.parse(reader.result)); });
    reader.readAsText(exported);
    // FileReader in jsdom schedules a browser task.
    jest.useRealTimers();
    expect(await result).toEqual({reference_size:[1280,720],polygon:[[.1,.1],[.9,.1],[.9,.9]]});
    document.getElementById('finish').click();
    expect(document.getElementById('save').disabled).toBe(false);
    add(138,92); add(266,92);
    expect(document.getElementById('save').disabled).toBe(true);
    add(266,164);
    expect(document.getElementById('save').disabled).toBe(false);
    document.getElementById('save').click();
    const secondReader = new FileReader();
    const second = new Promise(resolve => { secondReader.onload=()=>resolve(JSON.parse(secondReader.result)); });
    secondReader.readAsText(exported);
    expect((await second).polygons).toHaveLength(2);
    document.getElementById('clear').click();
    expect(document.getElementById('save').disabled).toBe(true);
    await new Promise(resolve => setTimeout(resolve, 1100));
  } finally {
    jest.useRealTimers();
    global.Image=originalImage;
    URL.createObjectURL=originalCreate;
    URL.revokeObjectURL=originalRevoke;
    click.mockRestore();
  }
});
