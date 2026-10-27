import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import com.google.gson.*;
import java.util.*;
import java.nio.file.*;
public class InitializerSensitivePaths extends GhidraScript {
 public void run() throws Exception {
  Set<String> roots=new HashSet<>();int missing=0;
  for(long va=0x82cb3628L;va<0x82cb42a4L;va+=4){long p=Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(va)))&~1L;String a=toAddr(p).toString();roots.add(a);if(getFunctionAt(toAddr(p))==null)missing++;}
  ArrayDeque<List<String>> queue=new ArrayDeque<>();int targets=0;
  FunctionIterator fs=currentProgram.getFunctionManager().getFunctions(true);
  while(fs.hasNext()){Function f=fs.next();String n=f.getName();
   if(n.startsWith("sceAppUtil")||n.startsWith("sceIo")||n.startsWith("sceFios")||n.startsWith("sceNet")||n.startsWith("sceNp")||n.startsWith("sceHttp")||n.startsWith("sceSsl")||n.equals("sceAppMgrLoadExec")||Set.of("fopen","fwrite","fflush","fclose","remove","rename").contains(n)){queue.add(List.of(f.getEntryPoint().toString()));targets++;}
  }
  Set<String> visited=new HashSet<>();List<Object> matches=new ArrayList<>();boolean capped=false;
  while(!queue.isEmpty()){
   monitor.checkCancelled();List<String> path=queue.remove();String a=path.get(path.size()-1);
   if(!visited.add(a))continue;if(visited.size()>50000){capped=true;break;}
   if(roots.contains(a)){List<String> forward=new ArrayList<>(path);Collections.reverse(forward);Map<String,Object> row=new LinkedHashMap<>();row.put("path",forward);Function target=getFunctionAt(toAddr(Long.parseUnsignedLong(path.get(0),16)));row.put("target_name",target==null?null:target.getName());matches.add(row);}
   if(path.size()-1>=3)continue;
   Function f=getFunctionAt(toAddr(Long.parseUnsignedLong(a,16)));if(f==null)continue;
   for(Function caller:f.getCallingFunctions(monitor)){List<String> next=new ArrayList<>(path);next.add(caller.getEntryPoint().toString());queue.add(next);}
  }
  Map<String,Object> out=new LinkedHashMap<>();out.put("scope","Existing Ghidra references only; up to 3 reverse edges, one representative shortest path per node; no indirect callback resolution, runtime effects or safety proof.");out.put("constructor_cells",799);out.put("unique_roots",roots.size());out.put("cells_without_defined_entry",missing);out.put("sensitive_target_functions",targets);out.put("visited",visited.size());out.put("capped",capped);out.put("matches",matches);
  Files.writeString(Path.of(getScriptArgs()[0]),new GsonBuilder().setPrettyPrinting().create().toJson(out));
 }
}
