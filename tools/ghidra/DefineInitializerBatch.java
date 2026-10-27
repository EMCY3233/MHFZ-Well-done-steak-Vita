import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.math.BigInteger;
import java.util.*;
import com.google.gson.*;
import java.nio.file.*;
public class DefineInitializerBatch extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();int first=Integer.parseInt(args[1]),count=Integer.parseInt(args[2]);
  if(first<0||count<1||count>64||first+count>799)throw new IllegalArgumentException("bounded batch required");
  List<Object> rows=new ArrayList<>();
  for(int i=first;i<first+count;i++){
   monitor.checkCancelled();long pointer=Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(0x82cb3628L+4L*i)));
   Address a=toAddr(pointer&~1L);Map<String,Object> row=new LinkedHashMap<>();row.put("index",i);row.put("entry",a.toString());
   try{
    Function f=getFunctionAt(a);
    if(f==null&&getFunctionContaining(a)!=null){row.put("status","inside_other_function");}
    else{
     if(f==null&&getInstructionAt(a)==null){
      currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"),a,a.add(1),BigInteger.valueOf(pointer&1));
      new DisassembleCommand(a,new AddressSet(a,a.add(0x800)),true).applyTo(currentProgram,monitor);
     }
     if(f==null&&getInstructionAt(a)!=null)f=createFunction(a,"initializer_"+i);
     row.put("status",f==null?"undefined":"defined");
     if(f!=null){row.put("body_bytes",f.getBody().getNumAddresses());List<String> calls=new ArrayList<>();for(Function c:f.getCalledFunctions(monitor))calls.add(c.getEntryPoint()+":"+c.getName());row.put("known_callees",calls);
      List<String> unresolved=new ArrayList<>();int computed=0;
      InstructionIterator instructions=currentProgram.getListing().getInstructions(f.getBody(),true);
      while(instructions.hasNext()){Instruction ins=instructions.next();if(!ins.getFlowType().isCall())continue;Address[] flows=ins.getFlows();if(flows.length==0)computed++;for(Address dest:flows)if(getFunctionAt(dest)==null)unresolved.add(ins.getAddress()+"->"+dest);}
      row.put("unresolved_direct_calls",unresolved);row.put("computed_calls",computed);
     }
    }
   }catch(Exception ex){row.put("status","error");row.put("error",ex.getClass().getSimpleName()+":"+ex.getMessage());}
   rows.add(row);
  }
  Files.writeString(Path.of(args[0]),new GsonBuilder().setPrettyPrinting().create().toJson(rows));
 }
}
