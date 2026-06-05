import React, { useState, useEffect } from 'react';
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function NurseryASTViewer({ examData, images }: { examData: any, images: any }) {
  const [questions, setQuestions] = useState<any[]>([]);

  useEffect(() => {
    if (examData?.questions) {
      setQuestions(examData.questions);
    }
  }, [examData]);

  if (!examData || !examData.questions) return null;

  const handleFeedback = async (index: number, action: 'edit' | 'simplify') => {
    const q = questions[index];
    let newInstruction = q.instruction;
    
    if (action === 'simplify') {
      newInstruction = prompt("Enter a simpler instruction for the children:", q.instruction) || q.instruction;
    } else {
      newInstruction = prompt("Edit the question instruction:", q.instruction) || q.instruction;
    }

    if (newInstruction === q.instruction) return; // no change

    const revisedQuestion = { ...q, instruction: newInstruction };
    
    // Update local state immediately
    const updated = [...questions];
    updated[index] = revisedQuestion;
    setQuestions(updated);

    // Send RLHF feedback to backend
    try {
      await fetch("/api/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          class_level: examData.class_level,
          learning_area: examData.learning_area,
          original_question: q,
          revised_question: revisedQuestion,
          action: action
        })
      });
      console.log("RLHF feedback submitted successfully");
    } catch (e) {
      console.error("Failed to submit RLHF feedback", e);
    }
  };

  const getImageUrl = (pic: string) => {
    if (!images || !pic) return null;
    const key = pic.toLowerCase();
    const found_key = images[key] ? key : (images[key.replace(/s$/, '')] ? key.replace(/s$/, '') : key + 's');
    const clean_key = found_key.replace(/[^a-z0-9]/g, '');
    return images[clean_key] || images[found_key] || images[key];
  };

  const renderQuestionContent = (q: any) => {
    const { type, content } = q;
    
    // We implement the most common question types mapped to the AST
    
    if (type === "count_circle" || type === "count_write") {
      return (
        <div className="flex flex-col gap-6 w-full">
          {content.items?.map((item: any, i: number) => (
            <div key={i} className="flex justify-between items-center w-full border-b-2 border-dotted border-gray-300 pb-4">
              <div className="flex flex-wrap gap-2">
                {Array.from({ length: item.count || 3 }).map((_, j) => (
                  <div key={j} className="w-16 h-16 bg-contain bg-center bg-no-repeat bg-gray-50 border border-gray-200 rounded-lg"
                       style={{ backgroundImage: getImageUrl(item.picture) ? `url(${getImageUrl(item.picture)})` : 'none' }}>
                    {!getImageUrl(item.picture) && <span className="text-[10px] text-gray-400 m-auto flex h-full items-center justify-center">{item.picture}</span>}
                  </div>
                ))}
              </div>
              <div className="text-4xl font-bold ml-8"> = ________ </div>
            </div>
          ))}
        </div>
      );
    }
    
    if (type === "draw_for_number") {
      return (
        <div className="flex flex-col gap-6 w-full">
          {content.numbers?.map((num: number, i: number) => (
            <div key={i} className="flex items-center gap-8 border-b-2 border-dotted border-gray-300 pb-4">
              <div className="text-6xl font-black">{num}</div>
              <div className="flex-1 min-h-[120px] border-[3px] border-dashed border-gray-400 rounded-xl bg-gray-50"></div>
            </div>
          ))}
        </div>
      );
    }
    
    if (type === "shade_for_number") {
      return (
        <div className="flex flex-col gap-6 w-full">
          {content.items?.map((item: any, i: number) => {
             const n = typeof item === 'number' ? item : (item.count || item.number || 3);
             const maxBoxes = Math.max(n + 2, 8);
             return (
               <div key={i} className="flex items-center gap-8 border-b-2 border-dotted border-gray-300 pb-4">
                 <div className="text-5xl font-black min-w-[50px]">{n}</div>
                 <div className="flex flex-wrap gap-2">
                   {Array.from({ length: maxBoxes }).map((_, j) => (
                     <div key={j} className={`w-12 h-12 border-2 border-black ${j < n ? 'bg-gray-300' : 'bg-white'}`}></div>
                   ))}
                 </div>
               </div>
             )
          })}
        </div>
      );
    }
    
    if (type === "match_numbers" || type === "match_words" || type === "match_pictures") {
      const renderMatchItem = (item: string) => {
        const imgUrl = getImageUrl(item);
        if (imgUrl) {
          return (
            <div className="w-24 h-24 bg-contain bg-center bg-no-repeat bg-white border-2 border-gray-200 rounded-lg shadow-sm"
                 style={{ backgroundImage: `url(${imgUrl})` }}>
            </div>
          );
        }
        return (
          <div className="text-2xl font-bold bg-white px-4 py-2 rounded-lg border-2 border-gray-200 shadow-sm">{item}</div>
        );
      };

      return (
        <div className="flex flex-col w-full max-w-2xl mx-auto my-8 gap-8">
          {Array.from({ length: Math.max(content.left?.length || 0, content.right?.length || 0) }).map((_, i) => (
            <div key={i} className="flex items-center justify-between w-full min-h-[96px]">
              {/* Left Side */}
              <div className="flex items-center justify-between w-[40%]">
                {content.left?.[i] ? renderMatchItem(content.left[i]) : <div></div>}
                {content.left?.[i] && <div className="w-4 h-4 bg-black rounded-full ml-4"></div>}
              </div>
              
              {/* Right Side */}
              <div className="flex items-center justify-between w-[40%] flex-row-reverse">
                {content.right?.[i] ? renderMatchItem(content.right[i]) : <div></div>}
                {content.right?.[i] && <div className="w-4 h-4 bg-black rounded-full mr-4"></div>}
              </div>
            </div>
          ))}
        </div>
      );
    }
    
    if (type === "add_numbers") {
      return (
        <div className="flex flex-col gap-6">
          {content.sums?.map((s: any, i: number) => (
            <div key={i} className="flex items-center gap-6 text-5xl font-black border-b-2 border-dotted border-gray-300 pb-4">
              <div className="w-16 text-center">{s.a}</div>
              <div className="text-gray-400">+</div>
              <div className="w-16 text-center">{s.b}</div>
              <div className="text-gray-400">=</div>
              <div className="w-32 border-b-4 border-black border-dotted h-12"></div>
            </div>
          ))}
        </div>
      );
    }
    
    if (type === "trace_letter" || type === "trace_number") {
      const charToTrace = content.letters?.[0] || content.numbers?.[0] || content.left?.[0] || "A";
      return (
         <div className="flex flex-col gap-8">
            <div className="text-[120px] leading-none font-black text-gray-200 tracking-widest border-b-[4px] border-dotted border-gray-400 pb-2 w-fit">
               {charToTrace} {charToTrace} {charToTrace}
            </div>
         </div>
      );
    }

    if (type === "sequence") {
      return (
        <div className="flex flex-col gap-6">
          {content.sequences?.map((seq: any, i: number) => (
            <div key={i} className="flex items-center gap-8 text-4xl font-bold">
              {seq.given?.map((g: number, j: number) => <span key={`g-${j}`}>{g}</span>)}
              <span className="w-24 border-b-4 border-black border-dotted">&nbsp;</span>
              {seq.after?.map((a: number, j: number) => <span key={`a-${j}`}>{a}</span>)}
            </div>
          ))}
        </div>
      );
    }
    
    if (type === "name_shapes") {
      return (
        <div className="flex justify-around items-end mt-8">
           {content.shapes?.map((shape: string, i: number) => (
              <div key={i} className="flex flex-col items-center gap-6">
                 {/* Very naive shape renderer fallback */}
                 <div className="w-24 h-24 border-[4px] border-black" style={{ borderRadius: shape.toLowerCase() === 'circle' ? '50%' : '0' }}></div>
                 <div className="w-32 border-b-[3px] border-dotted border-black h-8"></div>
              </div>
           ))}
        </div>
      )
    }

    if (type === "draw_colour") {
      return (
        <div className="flex flex-wrap gap-8 justify-center mt-6">
          {content.items?.map((item: any, i: number) => {
            const labelStr = typeof item === 'string' ? item : (item.picture || item.object || "Unknown");
            const key = labelStr.toLowerCase().replace("a picture of ", "").trim();
            const imgUrl = getImageUrl(key);
            return (
              <div key={i} className="flex flex-col items-center gap-4">
                <div className="w-64 h-64 border-2 border-dashed border-gray-400 rounded-xl bg-contain bg-center bg-no-repeat bg-gray-50 flex items-center justify-center p-2"
                     style={{ backgroundImage: imgUrl ? `url(${imgUrl})` : 'none' }}>
                  {!imgUrl && <span className="text-gray-400 text-sm">Draw/Colour here</span>}
                </div>
                <div className="text-3xl font-bold mt-4">{labelStr}</div>
              </div>
            );
          })}
        </div>
      );
    }

    if (type === "circle_correct") {
      const opts = content.options || content.items?.map((i:any)=>i.picture) || content.words || ["Option 1", "Option 2"];
      return (
        <div className="flex flex-col gap-6 mt-4">
          {content.task && (
            <div className="text-2xl font-semibold mb-4 text-gray-700">{content.task}</div>
          )}
          <div className="flex flex-wrap gap-8 justify-around w-full">
            {opts.map((opt: string, i: number) => {
              const imgUrl = getImageUrl(opt);
              return (
                <div key={i} className="flex flex-col items-center gap-4">
                  <div className="flex items-center justify-center font-black border-[4px] border-black rounded-full shadow-sm"
                       style={{
                          width: opt.length > 3 ? 'auto' : '100px',
                          height: opt.length > 3 ? '70px' : '100px',
                          padding: opt.length > 3 ? '0 40px' : '0',
                          fontSize: opt.length > 3 ? '32px' : '44px'
                       }}>
                    {opt}
                  </div>
                  {imgUrl && <img src={imgUrl} className="w-36 h-36 object-contain mt-4" alt={opt} />}
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    if (type === "copy_word") {
       return (
          <div className="flex flex-col gap-6 mt-4">
             {content.words?.map((w: string, i: number) => (
                <div key={i} className="flex items-center gap-6 mb-2">
                   <span className="text-4xl font-bold font-mono tracking-widest">{w}</span>
                   <div className="w-64 border-b-4 border-dotted border-black h-10"></div>
                </div>
             ))}
          </div>
       );
    }

    if (type === "odd_one_out") {
       return (
          <div className="flex flex-col gap-8 mt-4">
             {content.groups?.map((g: any, i: number) => (
                <div key={i} className="flex items-center justify-between border-b-2 border-dotted border-gray-300 pb-4 px-8">
                   {g.words?.map((w: string, j: number) => {
                      const imgUrl = getImageUrl(w);
                      return imgUrl ? (
                         <div key={j} className="w-36 h-36 bg-contain bg-center bg-no-repeat bg-white border-2 border-gray-200 rounded-lg shadow-sm"
                              style={{ backgroundImage: `url(${imgUrl})` }}>
                         </div>
                      ) : (
                         <span key={j} className="text-3xl font-bold bg-white px-6 py-3 rounded-lg border-2 border-gray-300 shadow-sm">{w}</span>
                      )
                   })}
                </div>
             ))}
          </div>
       );
    }

    if (type === "make_sentence") {
       return (
          <div className="flex flex-col gap-6 mt-4">
             <div className="flex flex-wrap gap-4">
               {content.words?.map((w: string, i: number) => (
                  <span key={i} className="text-2xl font-bold bg-gray-100 px-4 py-2 rounded-lg border border-gray-300">{w}</span>
               ))}
             </div>
             <div className="w-full border-b-[3px] border-dotted border-gray-500 h-16 mt-4"></div>
             <div className="w-full border-b-[3px] border-dotted border-gray-500 h-16"></div>
          </div>
       );
    }

    if (type === "write_number_names" || type === "write_in_words") {
       return (
          <div className="flex flex-col gap-6 mt-4 w-full">
             {content.pairs?.map((p: any, i: number) => (
                <div key={i} className="flex items-center gap-8 mb-4 border-b-2 border-dotted border-gray-300 pb-2">
                   <span className="text-5xl font-black w-24 text-right">{p.number}</span>
                   <div className="flex-1 border-b-[3px] border-dotted border-gray-500 h-10"></div>
                </div>
             ))}
          </div>
       );
    }

    if (type === "name_picture") {
      const pictures = content.items?.map((i:any) => i.picture) || content.words || [];
      return (
        <div className="flex flex-wrap gap-12 justify-around mt-8">
           {pictures.map((pic: string, i: number) => {
              const imgUrl = getImageUrl(pic);
              return (
                 <div key={i} className="flex flex-col items-center gap-6">
                    {imgUrl ? <img src={imgUrl} className="w-56 h-56 object-contain" /> : <div className="w-56 h-56 border-2 border-dashed border-gray-400 flex items-center justify-center text-sm text-gray-400">Picture</div>}
                    <div className="w-56 border-b-[4px] border-dotted border-gray-600 h-8"></div>
                 </div>
              )
           })}
        </div>
      );
    }

    if (type === "fill_missing_letter" || type === "fill_missing_word" || type === "write_correct_word" || type === "days_of_week") {
       return (
          <div className="flex flex-col gap-6 mt-6">
             {((content.words && content.words.length > 0) ? content.words : (content.items?.map((i:any) => typeof i === 'string' ? i : (i.word || i.picture || "")) || []))?.filter(Boolean).map((w: string, i: number) => {
                let displayWord = w;
                if (!w.includes('_') && type !== "write_correct_word") {
                   displayWord = w.split('').map((c, idx) => idx % 2 === 1 ? '_' : c).join('');
                }
                return (
                    <div key={i} className="text-[4rem] font-['Coming_Soon'] text-gray-700 tracking-[0.5em] ml-4">
                      {displayWord.split('').map((char, j) => (
                         <span key={j} className={char === '_' ? 'inline-block w-12 border-b-[5px] border-black mx-2' : ''}>
                            {char !== '_' ? char : ''}
                         </span>
                      ))}
                   </div>
                );
             })}
          </div>
       );
    }

    if (type === "number_between") {
       return (
          <div className="flex flex-col gap-6 mt-6">
             {content.sequences?.map((seq: any, i: number) => (
                <div key={i} className="flex items-end gap-6 font-['Coming_Soon'] text-5xl text-gray-600">
                   <div className="w-16 text-center">{seq.given?.[0] || seq.given?.[seq.given.length - 1]}</div>
                   <div className="w-24 border-b-4 border-dotted border-black h-12"></div>
                   <div className="w-16 text-center">{seq.after?.[0]}</div>
                </div>
             ))}
          </div>
       );
    }

    if (type === "name_sets") {
       return (
          <div className="flex flex-col gap-10 mt-6 w-full">
             {content.sets?.map((s: any, i: number) => {
                const imgUrl = getImageUrl(s.object);
                let count = 3;
                if (typeof s.count_word === 'number') count = s.count_word;
                else if (typeof s.count_word === 'string') {
                    const parsed = parseInt(s.count_word);
                    if (!isNaN(parsed)) count = parsed;
                }
                return (
                   <div key={i} className="flex items-center gap-8 border-b-2 border-dotted border-gray-300 pb-6">
                      <div className="flex flex-wrap gap-4 w-[280px] border-[3px] border-black rounded-2xl p-4 min-h-[140px] items-center justify-center">
                         {Array.from({length: count}).map((_, j) => (
                            imgUrl ? <img key={j} src={imgUrl} className="w-12 h-12 object-contain" /> : <div key={j} className="w-10 h-10 border-2 border-dashed border-gray-400"></div>
                         ))}
                      </div>
                      <div className="text-4xl font-black text-gray-500">=</div>
                      <div className="flex-1 border-b-[3px] border-dotted border-gray-500 h-12"></div>
                   </div>
                );
             })}
          </div>
       );
    }

    if (type === "write_yes_no") {
       const statements = content.statements || content.words || ["Is this correct?", "Is this wrong?"];
       return (
          <div className="flex flex-col gap-6 mt-6 w-full">
             {statements.map((stmt: string, i: number) => (
                <div key={i} className="flex items-center gap-8 border-b-[3px] border-dotted border-gray-300 pb-4">
                   <div className="text-3xl font-bold flex-1">{stmt}</div>
                   <div className="w-32 border-b-4 border-dotted border-black h-10"></div>
                </div>
             ))}
          </div>
       );
    }

    if (type === "oral_questions") {
       const statements = content.statements || content.words || ["What is your name?", "How old are you?"];
       return (
          <div className="flex flex-col gap-6 mt-6 w-full">
             {statements.map((stmt: string, i: number) => (
                <div key={i} className="flex items-start gap-6 border-b-2 border-dashed border-gray-200 pb-4">
                   <div className="text-2xl font-black mt-1 bg-gray-200 text-gray-700 rounded-full w-10 h-10 flex items-center justify-center shrink-0">{String.fromCharCode(97 + i)}</div>
                   <div className="text-3xl font-bold flex-1 italic text-gray-700">{stmt}</div>
                </div>
             ))}
          </div>
       );
    }

    // --- SMART GENERIC FALLBACK ---
    // If we haven't explicitly coded a React template for this new question type,
    // we use this smart fallback to render its contents dynamically instead of showing blank lines.
    
    // Helper to render unknown lists or objects
    const renderUnknownValue = (val: any, idx: number) => {
       if (typeof val === 'string' || typeof val === 'number') {
          // Check if the string is an image key
          if (typeof val === 'string' && getImageUrl(val.replace("a ", "").split(" ")[0])) {
             const img = getImageUrl(val.replace("a ", "").split(" ")[0]);
             return (
               <div key={idx} className="flex flex-col items-center gap-2 m-2">
                 <img src={img!} alt={val} className="w-24 h-24 object-contain" />
                  <span className="font-['Coming_Soon'] text-5xl text-gray-600">{val}</span>
               </div>
             );
          }
          return <div key={idx} className="font-bold text-2xl p-2 bg-gray-50 border border-gray-200 rounded m-1 inline-block">{val}</div>;
       }
       if (Array.isArray(val)) {
          return <div key={idx} className="flex flex-wrap gap-4 p-4 border-2 border-dashed border-gray-300 rounded-xl my-2">{val.map((v, i) => renderUnknownValue(v, i))}</div>;
       }
       if (typeof val === 'object' && val !== null) {
          return (
             <div key={idx} className="flex flex-col gap-2 p-4 border border-gray-300 rounded-xl bg-gray-50 w-full my-2">
                {Object.entries(val).map(([k, v], i) => (
                   <div key={i} className="flex items-start gap-4">
                      <span className="font-mono text-sm text-gray-500 uppercase tracking-widest mt-1 w-24 shrink-0">{k}:</span>
                      <div className="flex-1 flex flex-wrap">{renderUnknownValue(v, i)}</div>
                   </div>
                ))}
             </div>
          )
       }
       return null;
    };

    return (
      <div className="w-full flex flex-col gap-4 mt-6">
         {/* Render all keys dynamically */}
         {Object.entries(content).map(([key, value], i) => (
             <div key={i} className="w-full">
                {renderUnknownValue(value, i)}
             </div>
         ))}
         {/* Still provide a line just in case they need to write */}
         <div className="w-full border-b-[3px] border-dotted border-gray-400 h-10 mt-8"></div>
      </div>
    );
  };

  return (
    <div className="bg-white text-black p-12 max-w-[900px] mx-auto min-h-[1100px] shadow-2xl rounded-sm font-sans" style={{ printColorAdjust: 'exact', WebkitPrintColorAdjust: 'exact' }}>
      {/* Header */}
      <div className="flex flex-col items-center text-center border-b-4 border-black pb-6 mb-10">
        <h1 className="text-4xl font-black uppercase tracking-widest">{examData.school_name || "Nursery Exam"}</h1>
        <h2 className="text-2xl font-bold mt-2 uppercase tracking-wide">{examData.class_level} - {examData.la_name || examData.learning_area}</h2>
        <h3 className="text-lg font-bold mt-1 text-gray-600">{examData.term} - {examData.year}</h3>
        <div className="w-full flex justify-between mt-8 text-xl font-bold px-12">
           <div>NAME: _________________________________________</div>
           <div>DATE: ______________</div>
        </div>
      </div>

      {/* Questions */}
      <div className="flex flex-col gap-24 mt-10">
        {questions.map((q: any, index: number) => (
          <div key={index} className="flex flex-col w-full group relative bg-white border-[3px] border-dashed border-gray-200 rounded-[2.5rem] p-10 shadow-sm" style={{ breakInside: 'avoid' }}>
            
            {/* RLHF Feedback Controls (Visible on hover) */}
            <div className="absolute -left-16 top-0 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col gap-2">
              <button onClick={() => handleFeedback(index, 'edit')} className="bg-blue-100 text-blue-700 hover:bg-blue-200 px-2 py-1 rounded text-[10px] font-bold shadow-sm cursor-pointer" title="Edit text (RLHF)">Edit</button>
              <button onClick={() => handleFeedback(index, 'simplify')} className="bg-emerald-100 text-emerald-700 hover:bg-emerald-200 px-2 py-1 rounded text-[10px] font-bold shadow-sm cursor-pointer" title="Simplify text (RLHF)">Simplify</button>
            </div>

            <div className="flex items-start gap-6 w-full">
              <div className="text-3xl font-black mt-2 bg-gradient-to-br from-gray-800 to-black text-white rounded-2xl w-14 h-14 flex items-center justify-center shrink-0 shadow-md">
                {q.number || index + 1}
              </div>
              <div className="flex-1">
                <div className="text-4xl font-bold mb-10 text-gray-800">{q.instruction}</div>
                <div className="w-full pl-2 group-hover:opacity-90 transition-opacity">
                  {renderQuestionContent(q)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
