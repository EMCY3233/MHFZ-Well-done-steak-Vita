import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.pcode.*;
import com.google.gson.*;
import java.util.*;
import java.nio.file.*;
public class GetterAliasPcode extends GhidraScript {
 public void run() throws Exception {
  DecompInterface di=new DecompInterface();di.openProgram(currentProgram);
  Set<Function> callers=new LinkedHashSet<>();
  for(Reference ref:getReferencesTo(toAddr(0x8211b918L))){Function f=getFunctionContaining(ref.getFromAddress());if(f!=null)callers.add(f);}
  List<Object> rows=new ArrayList<>();int completed=0,roots=0;
  for(Function f:callers){
   if(f.getBody().getNumAddresses()>16000)continue;
   DecompileResults d=di.decompileFunction(f,20,monitor);if(!d.decompileCompleted()||d.getHighFunction()==null)continue;completed++;
   Iterator<PcodeOpAST> ops=d.getHighFunction().getPcodeOps();
   while(ops.hasNext()){
    PcodeOpAST op=ops.next();if(op.getOpcode()!=PcodeOp.CALL||op.getInput(0).getOffset()!=0x8211b918L||op.getOutput()==null)continue;roots++;
    Set<Varnode> seen=new HashSet<>();ArrayDeque<Varnode> queue=new ArrayDeque<>();queue.add(op.getOutput());
    while(!queue.isEmpty()&&seen.size()<256){
     Varnode v=queue.remove();if(!seen.add(v))continue;Iterator<PcodeOp> uses=v.getDescendants();
     while(uses.hasNext()){
      PcodeOp use=uses.next();int code=use.getOpcode();
      if((code==PcodeOp.COPY||code==PcodeOp.CAST)&&use.getInput(0)==v&&use.getOutput()!=null){queue.add(use.getOutput());continue;}
      if(code==PcodeOp.INT_ADD&&use.getOutput()!=null&&((use.getInput(0)==v&&use.getInput(1).isConstant()&&use.getInput(1).getOffset()==0)||(use.getInput(1)==v&&use.getInput(0).isConstant()&&use.getInput(0).getOffset()==0))){queue.add(use.getOutput());continue;}
      boolean store=code==PcodeOp.STORE&&use.getInput(1)==v;
      if(store||code==PcodeOp.CALL||code==PcodeOp.CALLIND||code==PcodeOp.MULTIEQUAL){
       Map<String,Object> row=new LinkedHashMap<>();row.put("caller",f.getEntryPoint().toString());row.put("getter_call",op.getSeqnum().getTarget().toString());row.put("use",use.getSeqnum().getTarget().toString());row.put("kind",use.getMnemonic());
       if(code==PcodeOp.CALL)row.put("callee",Long.toHexString(use.getInput(0).getOffset()));
       List<Integer> positions=new ArrayList<>();for(int i=0;i<use.getNumInputs();i++)if(use.getInput(i)==v)positions.add(i);row.put("alias_input_positions",positions);row.put("zero_offset_store",store);rows.add(row);
      }
     }
    }
   }
  }
  di.dispose();Map<String,Object> out=new LinkedHashMap<>();out.put("callers",callers.size());out.put("decompiled",completed);out.put("getter_roots",roots);out.put("scope","SSA COPY/CAST and exact zero-add only, PHI boundaries not propagated; no global aliases or interprocedural proof");out.put("uses",rows);
  Files.writeString(Path.of(getScriptArgs()[0]),new GsonBuilder().setPrettyPrinting().create().toJson(out));println("GETTER_ALIAS roots="+roots+" uses="+rows.size());
 }
}