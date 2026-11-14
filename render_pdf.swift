// Renders presentation.html to a PDF, one 1280x720 page per .slide.
// Usage: swift render_pdf.swift presentation.html out.pdf
import AppKit
import WebKit
import PDFKit

let args = CommandLine.arguments
let input = URL(fileURLWithPath: args[1]).standardizedFileURL
let output = URL(fileURLWithPath: args[2])

class Renderer: NSObject, WKNavigationDelegate {
    let web = WKWebView(frame: NSRect(x: 0, y: 0, width: 794, height: 1123))
    let doc = PDFDocument()
    override init() {
        super.init()
        web.navigationDelegate = self
        web.loadFileURL(input, allowingReadAccessTo: input.deletingLastPathComponent())
    }
    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        // white background between slides, no gaps
        let js = """
        document.documentElement.style.background='#fff';document.body.style.background='#fff';
        document.querySelectorAll('.slide').forEach(s=>s.style.margin='0');
        JSON.stringify([...document.querySelectorAll('.slide')].map(s=>{const r=s.getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,r.height]}))
        """
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
            webView.evaluateJavaScript(js) { result, err in
                guard let s = result as? String,
                      let data = s.data(using: .utf8),
                      let rects = try? JSONSerialization.jsonObject(with: data) as? [[Double]] else {
                    print("JS error", err as Any); exit(1)
                }
                self.render(rects, 0)
            }
        }
    }
    func render(_ rects: [[Double]], _ i: Int) {
        if i == rects.count {
            doc.write(to: output); print("wrote \(rects.count) pages to \(output.path)"); exit(0)
        }
        let cfg = WKPDFConfiguration()
        cfg.rect = CGRect(x: rects[i][0], y: rects[i][1], width: rects[i][2], height: rects[i][3])
        web.createPDF(configuration: cfg) { res in
            if case .success(let d) = res, let p = PDFDocument(data: d)?.page(at: 0) {
                self.doc.insert(p, at: self.doc.pageCount)
            } else { print("page \(i) failed: \(res)") }
            self.render(rects, i + 1)
        }
    }
}

let app = NSApplication.shared
let r = Renderer()
app.run()
