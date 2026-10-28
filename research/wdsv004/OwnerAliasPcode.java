import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.pcode.*;
import com.google.gson.*;
import java.util.*;
import java.nio.file.*;
public class OwnerAliasPcode extends GhidraScript {
 public void run() throws Exception {
  DecompInterface di=new DecompInterface();di.openProgram(currentProgram);
  Set<Function> callers=new LinkedHashSet<>();
  for(Reference ref:getReferencesTo(toAddr(0x839fd870L))){Function f=getFunctionContaining(ref.getFromAddress());if(f!=null)callers.add(f);}
  List<Object> rows=new ArrayList<>();int completed=0,roots=0;
  for(Function f:callers){
   if(f.getBody().getNumAddresses()>16000)continue;
   DecompileResults d=di.decompileFunction(f,20,monitor);if(!d.decompileCompleted()||d.getHighFunction()==null)continue;completed++;
   Set<Varnode> uniqueRoots=new HashSet<>();
   Iterator<PcodeOpAST> ops=d.getHighFunction().getPcodeOps();
   while(ops.hasNext()){
    PcodeOpAST op=ops.next();Varnode root=null;
    if(op.getOpcode()==PcodeOp.LOAD&&op.getInput(1).isConstant()&&op.getInput(1).getOffset()==0x839fd870L)root=op.getOutput();
    for(int ix=0;ix<op.getNumInputs();ix++){Varnode in=op.getInput(ix);if(in.isAddress()&&in.getAddress().isMemoryAddress()&&in.getOffset()==0x839fd870L)root=in;}
    if(root==null||!uniqueRoots.add(root))continue;roots++;
    Set<Varnode> seen=new HashSet<>();ArrayDeque<Varnode> queue=new ArrayDeque<>();queue.add(root);
    while(!queue.isEmpty()&&seen.size()<256){
     Varnode v=queue.remove();if(!seen.add(v))continue;Iterator<PcodeOp> uses=v.getDescendants();
     while(uses.hasNext()){
      PcodeOp use=uses.next();int code=use.getOpcode();
      if((code==PcodeOp.COPY||code==PcodeOp.CAST)&&use.getInput(0)==v&&use.getOutput()!=null){queue.add(use.getOutput());continue;}
      if((code==PcodeOp.INT_ADD||code==PcodeOp.PTRSUB)&&use.getOutput()!=null&&((use.getInput(0)==v&&use.getInput(1).isConstant()&&use.getInput(1).getOffset()==0)||(use.getInput(1)==v&&use.getInput(0).isConstant()&&use.getInput(0).getOffset()==0))){queue.add(use.getOutput());continue;}
      boolean store=code==PcodeOp.STORE&&use.getInput(1)==v;
      if(store||code==PcodeOp.CALL||code==PcodeOp.CALLIND||code==PcodeOp.MULTIEQUAL){
       Map<String,Object> row=new LinkedHashMap<>();row.put("caller",f.getEntryPoint().toString());row.put("owner_load",op.getSeqnum().getTarget().toString());row.put("use",use.getSeqnum().getTarget().toString());row.put("kind",use.getMnemonic());
       if(code==PcodeOp.CALL)row.put("callee",Long.toHexString(use.getInput(0).getOffset()));
       List<Integer> positions=new ArrayList<>();for(int i=0;i<use.getNumInputs();i++)if(use.getInput(i)==v)positions.add(i);row.put("alias_input_positions",positions);row.put("zero_offset_store",store);rows.add(row);
      }
     }
    }
   }
  }
  di.dispose();Map<String,Object> out=new LinkedHashMap<>();out.put("callers",callers.size());out.put("decompiled",completed);out.put("owner_roots",roots);out.put("scope","SSA memory input/LOAD roots; COPY/CAST and zero ADD/PTRSUB only, PHI boundaries not propagated; no global aliases or interprocedural proof");out.put("uses",rows);
  Files.writeString(Path.of(getScriptArgs()[0]),new GsonBuilder().setPrettyPrinting().create().toJson(out));println("OWNER_ALIAS roots="+roots+" uses="+rows.size());
 }
}