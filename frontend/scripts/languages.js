// Create slider row
function createSliderRow(lang) {
  return `
    <div class="flex flex-col w-full">
      <label class="mb-1">${lang}</label>
      <input
        type="range"
        min="0"
        max="7"
        value="0"
        class="w-full accent-blue-500"
      />
      <!-- Notch labels -->
      <div class="flex justify-between text-xs text-gray-600 mt-1">
        <span>0 yrs</span>
        <span>< 0.5 yrs</span>
        <span>< 1.0 yrs</span>
        <span>< 1.5 yrs</span>
        <span>< 2.0 yrs</span>
        <span>< 2.5 yrs</span>
        <span>< 3.0 yrs</span>
        <span>> 3.0 yrs</span>
      </div>
    </div>
  `;
}

// Inject HTML into containers
document.getElementById("javascript").innerHTML = createSliderRow("JavaScript");
document.getElementById("html_css").innerHTML = createSliderRow("HTML/CSS");
document.getElementById("sql").innerHTML = createSliderRow("SQL");
document.getElementById("python").innerHTML = createSliderRow("Python");
document.getElementById("bash_shell").innerHTML = createSliderRow("Bash/Shell");
document.getElementById("typescript").innerHTML = createSliderRow("TypeScript");
document.getElementById("java").innerHTML = createSliderRow("Java");
document.getElementById("csharp").innerHTML = createSliderRow("C#");
document.getElementById("cplusplus").innerHTML = createSliderRow("C++");
document.getElementById("powershell").innerHTML = createSliderRow("PowerShell");
document.getElementById("c").innerHTML = createSliderRow("C");
document.getElementById("php").innerHTML = createSliderRow("PHP");
document.getElementById("go").innerHTML = createSliderRow("Go");
document.getElementById("rust").innerHTML = createSliderRow("Rust");
document.getElementById("kotlin").innerHTML = createSliderRow("Kotlin");
document.getElementById("lua").innerHTML = createSliderRow("Lua");
document.getElementById("assembly").innerHTML = createSliderRow("Assembly");
document.getElementById("ruby").innerHTML = createSliderRow("Ruby");
document.getElementById("dart").innerHTML = createSliderRow("Dart");
document.getElementById("swift").innerHTML = createSliderRow("Swift");
document.getElementById("r").innerHTML = createSliderRow("R");
document.getElementById("groovy").innerHTML = createSliderRow("Groovy");
document.getElementById("visual_basic_dotnet").innerHTML = createSliderRow(
  "Visual Basic (.Net)"
);
document.getElementById("vba").innerHTML = createSliderRow("VBA");
document.getElementById("matlab").innerHTML = createSliderRow("MATLAB");
document.getElementById("perl").innerHTML = createSliderRow("Perl");
document.getElementById("gdscript").innerHTML = createSliderRow("GDScript");
document.getElementById("elixir").innerHTML = createSliderRow("Elixir");
document.getElementById("scala").innerHTML = createSliderRow("Scala");
document.getElementById("delphi").innerHTML = createSliderRow("Delphi");
document.getElementById("lisp").innerHTML = createSliderRow("Lisp");
document.getElementById("micropython").innerHTML =
  createSliderRow("MicroPython");
document.getElementById("zig").innerHTML = createSliderRow("Zig");
document.getElementById("erlang").innerHTML = createSliderRow("Erlang");
document.getElementById("fortran").innerHTML = createSliderRow("Fortran");
document.getElementById("ada").innerHTML = createSliderRow("Ada");
document.getElementById("fsharp").innerHTML = createSliderRow("F#");
document.getElementById("ocaml").innerHTML = createSliderRow("OCaml");
document.getElementById("gleam").innerHTML = createSliderRow("Gleam");
document.getElementById("prolog").innerHTML = createSliderRow("Prolog");
document.getElementById("cobol").innerHTML = createSliderRow("COBOL");
document.getElementById("mojo").innerHTML = createSliderRow("Mojo");
